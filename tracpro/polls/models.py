from __future__ import absolute_import, unicode_literals

from collections import Counter, OrderedDict
from itertools import chain, groupby
import json
from operator import itemgetter

import pytz

from django.conf import settings
from django.db import models, transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from tracpro.contacts.models import Contact

from . import rules
from .tasks import pollrun_start
from .utils import extract_words, natural_sort_key


class PollQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def by_org(self, org):
        return self.filter(org=org)


class PollManager(models.Manager.from_queryset(PollQuerySet)):

    def from_temba(self, org, temba_poll):
        """Create new or update existing Poll from RapidPro data."""
        poll, _ = self.get_or_create(org=org, flow_uuid=temba_poll.uuid)

        if poll.name == poll.rapidpro_name:
            # Name is tracking RapidPro name so we must update both.
            poll.name = poll.rapidpro_name = temba_poll.name
        else:
            # Custom name will be maintained despite update of RapidPro name.
            poll.rapidpro_name = temba_poll.name

        poll.save()

        # Sync related Questions, and maintain question order.
        temba_questions = temba_poll.rulesets
        temba_questions = OrderedDict((r.uuid, r) for r in temba_poll.rulesets)

        # Remove Questions that are no longer on RapidPro.
        poll.questions.exclude(ruleset_uuid__in=temba_questions.keys()).delete()

        # Create new or update existing Questions to match RapidPro data.
        for order, temba_question in enumerate(temba_questions.values(), 1):
            Question.objects.from_temba(poll, temba_question, order)

        return poll

    @transaction.atomic
    def set_active_for_org(self, org, uuids):
        """Set matching org Polls to be active, and all others to be inactive.

        If an invalid UUID is given, a ValueError is raised and the transaction
        is rolled back.
        """
        active_count = org.polls.filter(flow_uuid__in=uuids).update(is_active=True)
        if active_count != len(uuids):
            invalid_uuids = set(uuids) - set(org.polls.values_list('flow_uuid', flat=True))
            raise ValueError(
                "No Poll for {} matching these UUIDS: {}".format(
                    org.name, invalid_uuids))
        org.polls.exclude(flow_uuid__in=uuids).update(is_active=False)

    def sync(self, org):
        """Update the org's Polls and Questions from RapidPro."""
        # Retrieve current Polls known to RapidPro.
        temba_polls = org.get_temba_client().get_flows(archived=False)
        temba_polls = {p.uuid: p for p in temba_polls}

        # Remove Polls that are no longer on RapidPro.
        org.polls.exclude(flow_uuid__in=temba_polls.keys()).delete()

        # Create new or update existing Polls to match RapidPro data.
        for temba_poll in temba_polls.values():
            Poll.objects.from_temba(org, temba_poll)


@python_2_unicode_compatible
class Poll(models.Model):
    """Corresponds to a RapidPro flow.

    Keeping track of contact responses to a flow is data-intensive, so Tracpro
    only tracks flows that the user has selected. Selected flows are managed
    as Polls.
    """
    flow_uuid = models.CharField(max_length=36)
    org = models.ForeignKey(
        'orgs.Org', related_name='polls', verbose_name=_('org'))
    rapidpro_name = models.CharField(
        max_length=64, verbose_name=_('RapidPro name'))
    name = models.CharField(
        max_length=64, blank=True, verbose_name=_('name'))

    # Set this to False rather than deleting a Poll. If the user should
    # re-select the corresponding flow later, we can avoid re-importing
    # existing data.
    is_active = models.BooleanField(
        default=False, verbose_name=_("show on TracPro"))

    objects = PollManager()

    class Meta:
        unique_together = (
            ('org', 'flow_uuid'),
        )

    def __init__(self, *args, **kwargs):
        """Name should default to the RapidPro name."""
        super(Poll, self).__init__(*args, **kwargs)
        self.name = self.name or self.rapidpro_name

    def __str__(self):
        return self.name

    def get_flow_definition(self):
        """Retrieve extra metadata about the RapidPro flow."""
        if not hasattr(self, '_flow_definition'):
            # NOTE: Flow definition endpoint is not documented in the
            # RapidPro API docs.
            client = self.org.get_temba_client()
            definition = client.get_flow_definition(self.flow_uuid)
            self._flow_definition = definition
        return self._flow_definition

    def save(self, *args, **kwargs):
        """Don't save custom name if it is the same as the RapidPro name.

        This allows us to track changes to the name on RapidPro.
        """
        self.name = "" if self.name == self.rapidpro_name else self.name.strip()
        super(Poll, self).save(*args, **kwargs)
        self.name = self.name or self.rapidpro_name


class QuestionQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)


class QuestionManager(models.Manager.from_queryset(QuestionQuerySet)):

    def from_temba(self, poll, temba_question, order):
        """Create new or update existing Question from RapidPro data."""
        question, _ = self.get_or_create(poll=poll, ruleset_uuid=temba_question.uuid)

        if question.name == question.rapidpro_name:
            # Name is tracking RapidPro name so we must update both.
            question.name = question.rapidpro_name = temba_question.label
        else:
            # Custom name will be maintained despite update of RapidPro name.
            question.rapidpro_name = temba_question.label

        # Save the rules used to categorize answers to this question.
        rules = []
        for rule_set in question.poll.get_flow_definition().rule_sets:
            if rule_set['uuid'] == question.ruleset_uuid:  # Find the first matching rule set.
                for rule in rule_set['rules'][:-1]:  # The last rule is always "Other".
                    rules.append({
                        'category': rule['category'],
                        'test': rule['test'],
                    })
                break
        question.json_rules = json.dumps(rules)

        # The user can alter or correct the question's type after it is
        # initially set, so we shouldn't override the existing type.
        if not question.question_type:
            question.question_type = question.guess_question_type()

        question.order = order
        question.save()

        return question


@python_2_unicode_compatible
class Question(models.Model):
    """Corresponds to RapidPro RuleSet."""
    TYPE_OPEN = 'O'
    TYPE_MULTIPLE_CHOICE = 'C'
    TYPE_NUMERIC = 'N'
    TYPE_MENU = 'M'
    TYPE_KEYPAD = 'K'
    TYPE_RECORDING = 'R'
    TYPE_CHOICES = (
        (TYPE_OPEN, _("Open Ended")),
        (TYPE_MULTIPLE_CHOICE, _("Multiple Choice")),
        (TYPE_NUMERIC, _("Numeric")),
        (TYPE_MENU, _("Menu")),
        (TYPE_KEYPAD, _("Keypad")),
        (TYPE_RECORDING, _("Recording")),
    )

    ruleset_uuid = models.CharField(max_length=36)
    poll = models.ForeignKey(
        'polls.Poll', related_name='questions', verbose_name=_('poll'))
    rapidpro_name = models.CharField(
        max_length=64, verbose_name=_('RapidPro name'))
    name = models.CharField(
        max_length=64, blank=True, verbose_name=_('name'))
    question_type = models.CharField(
        max_length=1, choices=TYPE_CHOICES, verbose_name=_('question type'))
    order = models.IntegerField(
        default=0, verbose_name=_('order'))
    is_active = models.BooleanField(
        default=True, verbose_name=_("show on TracPro"))
    json_rules = models.TextField(
        blank=True,
        verbose_name=_("RapidPro rules"))

    objects = QuestionManager()

    class Meta:
        ordering = ('order',)
        unique_together = (
            ('ruleset_uuid', 'poll'),
        )

    def __init__(self, *args, **kwargs):
        """Name should default to the RapidPro name."""
        super(Question, self).__init__(*args, **kwargs)
        self.name = self.name or self.rapidpro_name

    def __str__(self):
        return self.name

    def categorize(self, value):
        """Return the first category that the value matches."""
        for rule in self.get_rules():
            if rules.passes_test(value, rule):
                return rules.get_category(rule)
        return "Other"

    def get_rules(self):
        if not hasattr(self, "_rules"):
            self._rules = json.loads(self.json_rules) if self.json_rules else []
        return self._rules

    def guess_question_type(self):
        """Inspect rules applied to question input to guess data type.

        Historically, the "response_type" field on the ruleset was used to
        determine question type. This field appears to have been deprecated
        and currently returns from a limited subset of possible types.
        """
        # Collect the type of each test applied to question input, e.g.,
        # "has any of these words", "has a number", "has a number between", etc.
        tests = [rule['test']['type'] for rule in self.get_rules()]

        if not tests:
            return self.TYPE_OPEN
        elif all(t in rules.NUMERIC_TESTS for t in tests):
            return self.TYPE_NUMERIC
        else:
            return self.TYPE_MULTIPLE_CHOICE

    def save(self, *args, **kwargs):
        """Don't save custom name if it is the same as the RapidPro name.

        This allows us to track changes to the name on RapidPro.
        """
        self.name = "" if self.name == self.rapidpro_name else self.name.strip()
        super(Question, self).save(*args, **kwargs)
        self.name = self.name or self.rapidpro_name


class PollRunQuerySet(models.QuerySet):

    def active(self):
        """Return all active PollRuns."""
        return self.filter(poll__is_active=True)

    def by_dates(self, start_date=None, end_date=None):
        pollruns = self.all()
        if start_date:
            pollruns = pollruns.filter(conducted_on__gte=start_date)
        if end_date:
            pollruns = pollruns.filter(conducted_on__lt=end_date)
        return pollruns

    def by_region(self, region, include_subregions=True):
        """Return all PollRuns for the region."""
        if not region:
            return self.all()

        q = Q(region=region)

        # Include PollRuns that include this region as a sub-region.
        q |= Q(region__in=region.get_ancestors(),
               pollrun_type=PollRun.TYPE_PROPAGATED)

        # Include poll runs that weren't sent to a particular region.
        q |= Q(region=None)

        # Include PollRuns that were sent to the region's sub-regions.
        if include_subregions:
            q |= Q(region__in=region.get_descendants())

        return self.filter(q)

    def by_org(self, org):
        return self.filter(poll__org=org)

    def universal(self):
        types = (PollRun.TYPE_UNIVERSAL, PollRun.TYPE_SPOOFED)
        return self.filter(pollrun_type__in=types)


class PollRunManager(models.Manager.from_queryset(PollRunQuerySet)):

    def create(self, poll, region=None, **kwargs):
        if region and poll.org != region.org:
            raise ValueError("Region org must match poll org.")
        return super(PollRunManager, self).create(poll=poll, region=region, **kwargs)

    def create_regional(self, region, do_start=True, **kwargs):
        """Create a poll run for a single region."""
        if not region:
            raise ValueError("Regional poll requires a non-null region.")
        kwargs['pollrun_type'] = PollRun.TYPE_REGIONAL
        pollrun = self.create(region=region, **kwargs)
        if do_start:
            pollrun_start.delay(pollrun.pk)
        return pollrun

    def create_propagated(self, region, do_start=True, **kwargs):
        """Create a poll run for a region and its sub-regions."""
        if not region:
            raise ValueError("Propagated poll requires a non-null region.")
        kwargs['pollrun_type'] = PollRun.TYPE_PROPAGATED
        pollrun = self.create(region=region, **kwargs)
        if do_start:
            pollrun_start.delay(pollrun.pk)
        return pollrun

    def create_spoofed(self, **kwargs):
        kwargs['pollrun_type'] = PollRun.TYPE_SPOOFED
        return self.create(**kwargs)

    def get_or_create_universal(self, poll, for_date=None, **kwargs):
        """Create a poll run that is for all regions."""
        # Get the requested date in the org timezone
        for_date = for_date or timezone.now()
        org_timezone = pytz.timezone(poll.org.timezone)
        for_local_date = for_date.astimezone(org_timezone).date()

        # look for a non-regional pollrun on that date
        sql = ('SELECT * FROM polls_pollrun WHERE poll_id = %s AND '
               'region_id IS NULL AND DATE(conducted_on AT TIME ZONE %s) = %s')
        params = [poll.pk, org_timezone.zone, for_local_date]
        existing = list(PollRun.objects.raw(sql, params))
        if existing:
            return existing[0]

        kwargs['poll'] = poll
        kwargs['region'] = None
        kwargs['pollrun_type'] = PollRun.TYPE_UNIVERSAL
        kwargs['conducted_on'] = for_date
        return self.create(**kwargs)

    def get_all(self, org, region, include_subregions=True):
        """
        Get all active PollRuns for the region, plus sub-regions if
        specified.
        """
        qs = self.get_queryset().active().by_org(org)
        qs = qs.select_related('poll', 'region')
        qs = qs.by_region(region, include_subregions)
        return qs


@python_2_unicode_compatible
class PollRun(models.Model):
    """Associates polls conducted on the same day."""

    TYPE_UNIVERSAL = 'u'  # Sent to all active regions.
    TYPE_SPOOFED = 's'  # Universal PollRun created by baseline data spoof.
    TYPE_REGIONAL = 'r'  # Sent to only one region.
    TYPE_PROPAGATED = 'p'  # Sent to one region and its sub-regions.
    TYPE_CHOICES = (
        (TYPE_UNIVERSAL, _('Universal')),
        (TYPE_SPOOFED, _('Spoofed')),
        (TYPE_REGIONAL, _('Single Region')),
        (TYPE_PROPAGATED, _('Propagated to sub-children')),
    )

    pollrun_type = models.CharField(
        max_length=1, editable=False, choices=TYPE_CHOICES)

    poll = models.ForeignKey('polls.Poll', related_name='pollruns')

    region = models.ForeignKey(
        'groups.Region', blank=True, null=True,
        help_text=_("Region where the poll was conducted."))

    conducted_on = models.DateTimeField(
        help_text=_("When the poll was conducted"), default=timezone.now)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="pollruns_created")

    objects = PollRunManager()

    def __str__(self):
        return "{poll} ({when})".format(
            poll=self.poll.name,
            when=self.conducted_on.strftime(settings.SITE_DATE_FORMAT),
        )

    def as_json(self, region=None, include_subregions=True):
        return {
            'id': self.pk,
            'poll': {
                'id': self.poll.pk,
                'name': self.poll.name,
            },
            'conducted_on': self.conducted_on,
            'region': {'id': self.region.pk, 'name': self.region.name} if self.region else None,
            'responses': self.get_response_counts(region, include_subregions),
        }

    def covers_region(self, region, include_subregions):
        """Return whether this PollRun is related to all given regions."""
        if not region or region.pk == self.region_id:
            # Shortcut to minimize more expensive queries later.
            return True

        if self.pollrun_type in (self.TYPE_UNIVERSAL, self.TYPE_SPOOFED):
            return True
        if self.pollrun_type == self.TYPE_REGIONAL:
            if include_subregions:
                return region in self.region.get_ancestors()
            else:  # pragma: nocover
                return region == self.region
        if self.pollrun_type == self.TYPE_PROPAGATED:
            if include_subregions:
                return region in self.region.get_family()
            else:
                return region in self.region.get_descendants()

    def get_responses(self, region=None, include_subregions=True,
                      include_empty=True):
        """Return all PollRun responses for this region and sub-regions."""
        if not self.covers_region(region, include_subregions):
            raise ValueError(
                "Request for responses in region where poll wasn't conducted")
        responses = self.responses.filter(
            is_active=True,
            contact__region__is_active=True,
            contact__is_active=True)  # Filter out inactive contacts
        if region:
            if include_subregions:
                regions = region.get_descendants(include_self=True)
                responses = responses.filter(contact__region__in=regions)
            else:
                responses = responses.filter(contact__region=region)
        if not include_empty:
            responses = responses.exclude(status=Response.STATUS_EMPTY)
        return responses.select_related('contact')

    def get_response_counts(self, region=None, include_subregions=True):
        """Returns PollRun response counts for this region and sub-regions."""
        status_counts = self.get_responses(region, include_subregions)
        status_counts = status_counts.values('status')
        status_counts = status_counts.annotate(count=Count('status'))
        results = {status[0]: 0 for status in Response.STATUS_CHOICES}
        results.update({sc['status']: sc['count'] for sc in status_counts})
        return results

    def is_last_for_region(self, region):
        """Return whether this was the last PollRun conducted in the region.

        Includes universal PollRuns.
        """
        if not self.covers_region(region, include_subregions=False):
            return False
        newer_pollruns = PollRun.objects.filter(
            poll=self.poll,
            conducted_on__gt=self.conducted_on,
        ).by_region(region, include_subregions=False)
        return not newer_pollruns.exists()


class ResponseQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def group_counts(self, *fields):
        """Group responses by the given fields then map to the count of matching responses."""
        responses = self.order_by(*fields).values(*fields)
        data = {}
        for field_values, _responses in groupby(responses, itemgetter(*fields)):
            data[field_values] = len(list(_responses))
        return data


class Response(models.Model):
    """Corresponds to RapidPro FlowRun."""
    STATUS_EMPTY = 'E'
    STATUS_PARTIAL = 'P'
    STATUS_COMPLETE = 'C'
    STATUS_CHOICES = (
        (STATUS_EMPTY, _("Empty")),
        (STATUS_PARTIAL, _("Partial")),
        (STATUS_COMPLETE, _("Complete")),
    )

    flow_run_id = models.IntegerField(null=True)

    pollrun = models.ForeignKey('polls.PollRun', null=True, related_name='responses')

    contact = models.ForeignKey('contacts.Contact', related_name='responses')

    created_on = models.DateTimeField(
        help_text=_("When this response was created"))

    updated_on = models.DateTimeField(
        help_text=_("When the last activity on this response was"))

    status = models.CharField(
        max_length=1, verbose_name=_("Status"), choices=STATUS_CHOICES,
        help_text=_("Current status of this response"))

    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this response is active"))

    objects = ResponseQuerySet.as_manager()

    class Meta:
        unique_together = [
            ('flow_run_id', 'pollrun'),
        ]

    @classmethod
    def create_empty(cls, org, pollrun, run):
        """
        Creates an empty response from a run. Used to start or restart a
        contact in an existing pollrun.
        """
        contact = Contact.get_or_fetch(org, uuid=run.contact)

        # de-activate any existing responses for this contact
        pollrun.responses.filter(contact=contact).update(is_active=False)

        return Response.objects.create(
            flow_run_id=run.id, pollrun=pollrun, contact=contact,
            created_on=run.created_on, updated_on=run.created_on,
            status=Response.STATUS_EMPTY)

    @classmethod
    def from_run(cls, org, run, poll=None):
        """
        Gets or creates a response from a flow run. If response is not
        up-to-date with provided run, then it is updated. If the run doesn't
        match with an existing poll pollrun, it's assumed to be non-regional.
        """
        response = Response.objects.filter(pollrun__poll__org=org, flow_run_id=run.id)
        response = response.select_related('pollrun').first()
        run_updated_on = cls.get_run_updated_on(run)

        # if there is an up-to-date existing response for this run, return it
        if response and response.updated_on == run_updated_on:
            return response

        if not poll:
            poll = Poll.objects.active().by_org(org).get(flow_uuid=run.flow)

        contact = Contact.get_or_fetch(poll.org, uuid=run.contact)

        # categorize completeness
        if run.completed:
            status = Response.STATUS_COMPLETE
        elif run.values:
            status = Response.STATUS_PARTIAL
        else:
            status = Response.STATUS_EMPTY

        if response:
            # clear existing answers which will be replaced
            response.answers.all().delete()

            response.updated_on = run_updated_on
            response.status = status
            response.save(update_fields=('updated_on', 'status'))
        else:
            # if we don't have an existing response, then this poll started in
            # RapidPro and is non-regional
            pollrun = PollRun.objects.get_or_create_universal(
                poll=poll,
                for_date=run.created_on,
            )

            # if contact has an older response for this pollrun, retire it
            Response.objects.filter(pollrun=pollrun, contact=contact).update(is_active=False)

            response = Response.objects.create(
                flow_run_id=run.id, pollrun=pollrun, contact=contact,
                created_on=run.created_on, updated_on=run_updated_on,
                status=status)
            response.is_new = True

        # organize values by ruleset UUID
        questions = poll.questions.active()
        valuesets_by_ruleset = {valueset.node: valueset for valueset in run.values}
        valuesets_by_question = {q: valuesets_by_ruleset.get(q.ruleset_uuid, None)
                                 for q in questions}

        # convert valuesets to answers
        for question, valueset in valuesets_by_question.iteritems():
            if valueset:
                Answer.objects.create(
                    response=response,
                    question=question,
                    value=valueset.value,
                    category=valueset.category,
                    submitted_on=valueset.time,
                )

        return response

    @classmethod
    def get_run_updated_on(cls, run):
        # find the valueset with the latest time
        last_value_on = None
        for valueset in run.values:
            if not last_value_on or valueset.time > last_value_on:
                last_value_on = valueset.time

        return last_value_on if last_value_on else run.created_on


class AnswerQuerySet(models.QuerySet):

    def word_counts(self):
        answers = self.values_list('value', 'response__contact__language')
        words = [extract_words(*a) for a in answers]
        counts = Counter(chain(*words))
        return counts.most_common(50)

    def group_values(self, *fields):
        """Group answers by the given fields then map to a list of matching values."""
        answers = self.order_by(*fields).values('value', *fields)
        data = {}
        for field_values, _answers in groupby(answers, itemgetter(*fields)):
            data[field_values] = [a['value'] for a in _answers]
        return data

    def category_counts(self):
        categories = self.values_list('category', flat=True)
        counts = Counter(categories)
        return counts.most_common()

    def category_counts_by_pollrun(self):
        counts = []
        answers = self.order_by('category').values('category', 'response__pollrun')
        for category, _answers in groupby(answers, itemgetter('category')):
            pollrun_counts = Counter(a['response__pollrun'] for a in _answers)
            counts.append((category, pollrun_counts))

        # Order the data by the category name.
        counts.sort(key=lambda (category, pollrun_counts): natural_sort_key(category))
        return counts


class AnswerManager(models.Manager.from_queryset(AnswerQuerySet)):

    def create(self, category, **kwargs):
        # category can be a string or a multi-language dict
        if isinstance(category, dict):
            if 'base' in category:
                category = category['base']
            else:
                category = category.itervalues().next()

        if category == 'All Responses':
            category = None

        return super(AnswerManager, self).create(category=category, **kwargs)


class Answer(models.Model):
    """Corresponds to RapidPro FlowStep."""

    response = models.ForeignKey('polls.Response', related_name='answers')
    question = models.ForeignKey('polls.Question', related_name='answers')
    value = models.CharField(max_length=640, null=True)
    category = models.CharField(max_length=36, null=True)
    submitted_on = models.DateTimeField(
        help_text=_("When this answer was submitted"))

    objects = AnswerManager()
