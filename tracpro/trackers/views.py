from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartCRUDL, SmartListView, SmartCreateView

from .forms import GroupRuleFormSet
from .models import Tracker, GroupRule


class TrackerCRUDL(SmartCRUDL):
    model = Tracker
    actions = ('create', 'list')

    class List(OrgPermsMixin, SmartListView):
        permission = 'trackers.tracker_list'

    class Create(OrgPermsMixin, SmartCreateView):
        title = _("Tracker configuration")
        success_message = _("Your new tracker and group rules have been created")

        def get_context_data(self, **kwargs):
            context = super(TrackerCRUDL.Create, self).get_context_data(**kwargs)
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
            for group_rule_form in group_rule_formset:
                group_rule = group_rule_form.save(commit=False)
                group_rule.tracker = self.object
                group_rule.save()

            return HttpResponseRedirect(self.get_success_url())


class GroupRuleCRUDL(SmartCRUDL):
    model = GroupRule
    actions = ('create', 'list')
