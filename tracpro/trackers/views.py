from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartCRUDL, SmartListView, SmartCreateView, SmartUpdateView

from .forms import GroupRuleFormSet, TrackerForm
from .models import Tracker, GroupRule


class TrackerCRUDL(SmartCRUDL):
    model = Tracker
    actions = ('create', 'list', 'update')

    class List(OrgPermsMixin, SmartListView):
        permission = 'trackers.tracker_list'

    class Update(OrgPermsMixin, SmartUpdateView):
        title = _("Tracker configuration")
        success_message = _("Your new tracker and group rules have been updated")
        form_class = TrackerForm

        def dispatch(self, *args, **kwargs):
            self.object = self.get_object()
            self.form = self.get_form()
            return super(TrackerCRUDL.Update, self).dispatch(*args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(TrackerCRUDL.Update, self).get_context_data(**kwargs)
            if 'group_rule_formset' not in context:
                context['group_rule_formset'] = GroupRuleFormSet(queryset=context['tracker'].group_rules.all())
            return context

        def post(self, request, *args, **kwargs):
            form = self.get_form_class()(request.POST, instance=self.object)
            group_rule_formset = GroupRuleFormSet(request.POST, queryset=self.object.group_rules.all())
            if form.is_valid() and group_rule_formset.is_valid():
                return self.form_valid(form, group_rule_formset)
            else:
                return self.form_invalid(form, group_rule_formset)

        def form_invalid(self, form, group_rule_formset):
            return self.render_to_response(self.get_context_data(form=form, group_rule_formset=group_rule_formset))

        def form_valid(self, form, group_rule_formset):
            self.object = form.save()
            group_rule_formset.save(commit=False)
            for obj in group_rule_formset.deleted_objects:
                obj.delete()
            for group_rule in group_rule_formset.new_objects:
                group_rule.tracker = self.object
                group_rule.save()
            for group_rule in group_rule_formset.changed_objects:
                group_rule[0].save()

            return HttpResponseRedirect(self.get_success_url())

    class Create(OrgPermsMixin, SmartCreateView):
        title = _("Tracker configuration")
        success_message = _("Your new tracker and group rules have been created")
        form_class = TrackerForm

        def dispatch(self, *args, **kwargs):
            self.object = None
            self.form = self.get_form()
            return super(TrackerCRUDL.Create, self).dispatch(*args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(TrackerCRUDL.Create, self).get_context_data(**kwargs)
            if 'group_rule_formset' not in context:
                data = {'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0'}
                context['group_rule_formset'] = GroupRuleFormSet(data)
            return context

        def post(self, request, *args, **kwargs):
            form = self.get_form_class()(request.POST)
            group_rule_formset = GroupRuleFormSet(request.POST)
            if form.is_valid() and group_rule_formset.is_valid():
                return self.form_valid(form, group_rule_formset)
            else:
                return self.form_invalid(form, group_rule_formset)

        def form_invalid(self, form, group_rule_formset):
            return self.render_to_response(self.get_context_data(form=form, group_rule_formset=group_rule_formset))

        def form_valid(self, form, group_rule_formset):
            self.object = form.save()
            group_rule_formset.save(commit=False)
            for group_rule in group_rule_formset.new_objects:
                group_rule.tracker = self.object
                group_rule.save()

            return HttpResponseRedirect(self.get_success_url())


class GroupRuleCRUDL(SmartCRUDL):
    model = GroupRule
    actions = ('create', 'list')
