from django.urls import path
from . import views

urlpatterns = [
    path('', views.LinkListCreateView.as_view(), name='link-list-create'),
    path('public/', views.PublicShortenView.as_view(), name='link-public-shorten'),
    path('claim/', views.ClaimLinksView.as_view(), name='link-claim'),
    path('<int:pk>/', views.LinkDetailView.as_view(), name='link-detail'),
]