from __future__ import absolute_import, unicode_literals

from .views import TrackerCRUDL, GroupRuleCRUDL

urlpatterns = TrackerCRUDL().as_urlpatterns()
urlpatterns += GroupRuleCRUDL().as_urlpatterns()
