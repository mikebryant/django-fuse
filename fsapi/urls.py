# These are actually paths on the UNIX filesystem

from django.conf.urls.defaults import *


urlpatterns = patterns('fsapi.views',
    url(r'^$', 'index'),

    url(r'^proc$', 'app_list'),
    url(r'^proc/(?P<app>\w+)$', 'model_list'),
    url(r'^proc/(?P<app>\w+)/(?P<model>\w+)$', 'model_index'),
    url(r'^proc/(?P<app>\w+)/(?P<model>\w+)/by-pk$', 'all_instances'),
    url(r'^proc/(?P<app>\w+)/(?P<model>\w+)/by-pk/(?P<pk>[^/]+)$', 'fields_for_model'),
    url(r'^proc/(?P<app>\w+)/(?P<model>\w+)/by-pk/(?P<pk>[^/]+)/(?P<field>[^/]+)$', 'modelfield_by_pk'),

)
