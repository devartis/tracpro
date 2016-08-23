from __future__ import absolute_import, unicode_literals

from .views import TrackerCRUDL, AlertCRUDL, OccurrenceCRUDL

urlpatterns = TrackerCRUDL().as_urlpatterns()
urlpatterns += AlertCRUDL().as_urlpatterns()
urlpatterns += OccurrenceCRUDL().as_urlpatterns()
