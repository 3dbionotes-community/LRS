from django.urls import include, path
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
    path('lrs/?action=refresh/', views.EntryListUpdateView.as_view()),
    path('lrs/<slug:query_id>/', views.EntryDetailView.as_view()),
    path('', include(router.urls)),
]
