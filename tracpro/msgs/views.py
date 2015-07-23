from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _

from dash.orgs.views import OrgPermsMixin
from dash.utils import get_obj_cacheable

from smartmin.users.views import SmartCRUDL, SmartListView, SmartCreateView

from tracpro.contacts.models import Contact
from tracpro.polls.models import PollRun
from .models import Message, InboxMessage


class MessageListMixin(object):
    field_config = {
        'text': {'class': 'italicized'},
        'cohort': {'label': _("Recipients")},
        'pollrun': {'label': _("Poll Run")},
    }
    default_order = ('-pk',)
    link_fields = ('pollrun',)

    def get_cohort(self, obj):
        return obj.get_cohort_display()

    def get_region(self, obj):
        return obj.region if obj.region else _("All")

    def lookup_field_link(self, context, field, obj):
        if field == 'pollrun':
            return reverse('polls.pollrun_read', args=[obj.pollrun.pk])

        return super(MessageListMixin, self).lookup_field_link(context, field, obj)


class MessageCRUDL(SmartCRUDL):
    model = Message
    actions = ('list', 'send', 'by_contact')

    class Send(OrgPermsMixin, SmartCreateView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            text = request.POST.get('text')
            cohort = request.POST.get('cohort')
            pollrun = PollRun.objects.get(poll__org=org, pk=request.POST.get('pollrun'))
            region = self.request.region

            msg = Message.create(org, self.request.user, text, pollrun, cohort, region)
            return JsonResponse(msg.as_json())

    class List(OrgPermsMixin, MessageListMixin, SmartListView):
        fields = ('sent_on', 'sent_by', 'pollrun', 'cohort', 'region', 'text')
        title = _("Message Log")

        def derive_queryset(self, **kwargs):
            return Message.get_all(self.request.org, self.request.region)

        def lookup_field_link(self, context, field, obj):
            return super(MessageCRUDL.List, self).lookup_field_link(context, field, obj)

    class ByContact(OrgPermsMixin, MessageListMixin, SmartListView):
        fields = ('sent_on', 'sent_by', 'pollrun', 'cohort', 'text')
        field_config = {
            'text': {'class': 'italicized'},
            'cohort': {'label': _("Recipients")},
            'pollrun': {'label': _("Poll Run")},
        }

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<contact>\d+)/$' % (path, action)

        def derive_contact(self):
            def fetch():
                return Contact.objects.get(pk=self.kwargs['contact'], org=self.request.org)
            return get_obj_cacheable(self, '_contact', fetch)

        def derive_queryset(self, **kwargs):
            return self.derive_contact().messages.all()

        def lookup_field_link(self, context, field, obj):
            return super(MessageCRUDL.ByContact, self).lookup_field_link(context, field, obj)

        def get_context_data(self, **kwargs):
            context = super(MessageCRUDL.ByContact, self).get_context_data(**kwargs)
            context['contact'] = self.derive_contact()
            return context

#class InboxMessageListMixin(object):
#    field_config = {
#        'text': {'class': 'italicized'},
#    }
#    default_order = ('-pk',)
#    link_fields = ('contact_from',)

#    def lookup_field_link(self, context, field, obj):
#        if field == 'contact_from':
#            return reverse('contacts.read', args=[obj.contact_from.pk])

#        return super(InboxMessageListMixin, self).lookup_field_link(context, field, obj)

# https://smartmin.readthedocs.org/en/latest/quickstart.html#permissions
class InboxMessageCRUDL(SmartCRUDL):
    actions = ('read', 'list')
    model = InboxMessage

    class List(SmartListView):
        fields = ('contact_from', 'text', 'archived', 'created_on', 'delivered_on', 'sent_on')
        default_order = '-created_on'