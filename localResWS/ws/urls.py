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
    path('lrs/<slug:query_id>/', views.EntryDetailView.as_view()),
    re_path(r'^lrs/fakeLR/(?P<pdb_id>\w{4})/(?P<chain_id>\w{1})/$', views.PdbEntryFakeView.as_view()),
    re_path(r'^lrs/localResolution/any/(?P<pdb_id>\w{4})/(?P<chain_id>\w{1})/$', views.PdbEntryLocResAnyAlgorithm.as_view()),
    re_path(r'^lrs/pdbAnnotFromMap/all/(?P<pdb_id>\w{4})/(?P<chain_id>\w{1})/$', views.PdbEntryAllAnnAlgorithm.as_view()),
    path('', include(router.urls)),
]
