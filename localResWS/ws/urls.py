from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from localResWS.ws import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'types', views.TypeViewSet)
router.register(r'lrs', views.EntryViewSet)
router.register(r'files', views.DataFileViewSet)
router.register(r'datasets', views.DataSetViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('lrs/update/', views.EntryListUpdateView.as_view(), name='db-update'),
    path('lrs/<slug:query_id>/', views.EntryAnnFromMapsView.as_view()),
    re_path(r'^lrs/fakeLR/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/$', views.PdbEntryFakeView.as_view()),
    re_path(r'^lrs/pdbAnnotFromMap/all/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/(?P<modified_model>(pdb-redo|isolde))?/$', views.PdbEntryAllAnnFromMapView.as_view()),
    re_path(r'^files/modifiedPdb/list/(?P<model_type>(pdb-redo|isolde))/(?P<pdb_id>\d\w{3})/$', views.ListModifiedPDBView.as_view()),
    re_path(r'^files/modifiedPdb/download/(?P<file_uuid>[0-9a-f-]+)/$', views.DownloadGenericFile.as_view()),
    re_path(r'^files/computModels/list/(?P<model_type>(SWISS-MODEL))/?(?P<uniprot_id>\w{4,12})/(?P<prot_name>\w{3,12})?/?(?P<model_name>\w{3,20})?/$', views.ListComputationalModelsView.as_view()),
    path('', include(router.urls)),
]
