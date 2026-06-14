from django.urls import path
from .views import PetListCreateView, PetDetailView

urlpatterns = [
    path('', PetListCreateView.as_view(), name='pet_list_create'),
    path('<uuid:pet_id>/', PetDetailView.as_view(), name='pet_detail'),
]
