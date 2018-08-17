from django.conf.urls import url
#from rest_framework.urlpatterns import format_suffix_patterns
from  .import views

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'getnmapdata/$',  views.nMapData,  name="nMapData"),
    url(r'getcertsdata/$', views.certsData, name="certsData"),
]
