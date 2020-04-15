from django.urls import path, include
from rest_framework.routers import DefaultRouter
from localResWS.ws import views

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('api/', include('rest_framework.urls', namespace='rest_framework')),
    # Volume maps
    path('lrs/', views.EntryList.as_view(), name='entry-list'),
]
