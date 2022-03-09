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
# 
router.register(r'uniprotEntries', views.UniprotEntryViewSet)
router.register(r'trackTypes', views.TrackTypeViewSet)
router.register(r'featureTracks', views.FeatureTracksViewSet)
router.register(r'featuresData', views.TrackDataViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),

    path('update/', views.EntryListUpdateView.as_view(), name='db-update'),
    path('<slug:query_id>/', views.EntryAnnFromMapsView.as_view()),

    # EM Validation annotations for 3DBionotes - Protvista 
    re_path(r'^pdbAnnotFromMap/all/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/?(?P<modified_model>(pdb-redo|isolde))?/$', views.PdbEntryAllAnnFromMapView.as_view()),

    
    re_path(r'^files/genericDownload/(?P<file_uuid>[0-9a-f-]+)/$', views.DownloadGenericFile.as_view()),
    re_path(r'^files/downloadModelAndLigand/(?P<experiment_name>(covid19_COSS))/(?P<pdb_id>(\d\w{3}))/'
            r'(?P<compound_id>\w{3,30})/(?P<pocket_id>\w{1,24})/?(?P<pose_id>\w{1,3})?/$', views.DownloadModelAndLigand.as_view()),

    re_path(r'^files/computModels/list/(?P<model_type>(SWISS-MODEL|BSM-Arc|AlphaFold))/?(?P<uniprot_id>\w{4,12})/?(?P<prot_name>\w{3,12})?/?(?P<model_name>\w{3,20})?/$', views.ListComputationalModelsView.as_view()),
    re_path(r'^files/pdbAndLigand/list/(?P<experiment_name>(Diamond_mainProtease|covid19_COSS))/(?P<pdb_id>(\d\w{3}|any))?/'
            r'?(?P<compound_id>\w{3,30})?/?(?P<pocket_id>\w{1,24})?/?(?P<pose_id>\w{1,3})?/$', views.ListPdbAndLigandView.as_view()),

    # /features/P0DTC1/Genomic_Variants_CNCB/
    re_path('^features/(?P<uniprot_entry>[^/.]+)/(?P<name>[^/.]+)/$', views.TrackDetailView.as_view()),
    # /features/variants/Genomic_Variants_CNCB/P0DTC1/
    re_path('^features/variants/(?P<name>[^/.]+)/(?P<uniprot_entry>[^/.]+)/$', views.TrackDetailView.as_view()),

    re_path(r'^files/computModels/(?P<model_type>[^/.]+)/(?P<model_name>[^/.]+)/$', views.DownloadComputationalModelsView.as_view()),
    
    # modifiedPdb
    re_path(r'^files/modifiedPdb/list/(?P<model_type>(pdb-redo|isolde|refmac))/(?P<pdb_id>\d\w{3})/$', views.ListModifiedPDBView.as_view()),
    re_path(r'^files/modifiedPdb/download/(?P<file_uuid>[0-9a-f-]+)/$', views.DownloadGenericFile.as_view()),
    re_path(r'^files/modifiedPdb/(?P<model_type>(pdb-redo|isolde|refmac))/(?P<model_name>[^/.]+)/$', views.DownloadModifiedPdbFile.as_view()),
]
