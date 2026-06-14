from django.urls import path
from .views import (
    SignupView, SigninView, ProfileImageUploadView, ProfileImageDeleteView,
    UserProfileView, VeterinarianProfileImageUploadView, VeterinarianProfileImageDeleteView,
    VeterinarianProfileUpdateView, VeterinarianListView,
    VeterinarianReviewListCreateView, VeterinarianReviewDetailView,
    UserReviewListView, AppointmentReviewView
)

urlpatterns = [
    # Authentication
    path('signup/', SignupView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/avatar/upload/', ProfileImageUploadView.as_view(), name='profile_image_upload'),
    path('profile/avatar/delete/', ProfileImageDeleteView.as_view(), name='profile_image_delete'),
    
    # Veterinarian Profile
    path('veterinarians/', VeterinarianListView.as_view(), name='veterinarian_list'),
    path('profile/vet/update/', VeterinarianProfileUpdateView.as_view(), name='vet_profile_update'),
    path('profile/vet/avatar/upload/', VeterinarianProfileImageUploadView.as_view(), name='vet_profile_image_upload'),
    path('profile/vet/avatar/delete/', VeterinarianProfileImageDeleteView.as_view(), name='vet_profile_image_delete'),
    
    # Reviews
    path('veterinarians/<int:veterinarian_id>/reviews/', VeterinarianReviewListCreateView.as_view(), name='vet_review_list_create'),
    path('reviews/<int:review_id>/', VeterinarianReviewDetailView.as_view(), name='vet_review_detail'),
    path('reviews/my/', UserReviewListView.as_view(), name='my_reviews'),
    path('appointments/<int:appointment_id>/review/', AppointmentReviewView.as_view(), name='appointment_review'),
]
