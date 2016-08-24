from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views
from .views import TrackerCRUDL, AlertCRUDL, OccurrenceCRUDL

urlpatterns = TrackerCRUDL().as_urlpatterns()
urlpatterns += AlertCRUDL().as_urlpatterns()
urlpatterns += OccurrenceCRUDL().as_urlpatterns()
urlpatterns += [
    url("^occurrences/(?P<alert_rule_id>\d+)/$",
        views.AlertRuleOccurrences.as_view(),
        name="occurrences-by-alert")
]
