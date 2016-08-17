from __future__ import absolute_import, unicode_literals

from .views import TrackerCRUDL, GroupRuleCRUDL, AlertCRUDL

urlpatterns = TrackerCRUDL().as_urlpatterns()
urlpatterns += GroupRuleCRUDL().as_urlpatterns()
urlpatterns += AlertCRUDL().as_urlpatterns()
