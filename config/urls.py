from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import (
    SignupView, SigninView, ProfileImageUploadView, ProfileImageDeleteView,
    UserProfileView, VeterinarianProfileImageUploadView, VeterinarianProfileImageDeleteView,
    VeterinarianProfileUpdateView, VeterinarianListView,
    VeterinarianReviewListCreateView, VeterinarianReviewDetailView,
    UserReviewListView, AppointmentReviewView, veterinarian_detail_page, book_appointment_page
)
from apps.appointments.views import AvailableTimeSlotsView, AppointmentListCreateView
from apps.payments.views import (
    CreateCheckoutSessionView, 
    payment_page, payment_success, payment_cancel, stripe_webhook
)

def index(request):
    return render(request, 'home/index.html')

def signup_page(request):
    return render(request, 'auth/signup.html')

def signin_page(request):
    return render(request, 'auth/signin.html')

def veterinarians_page(request):
    return render(request, 'veterinarians/list.html')

def vet_profile_complete_page(request):
    return render(request, 'veterinarians/profile_complete.html')

def my_pets_page(request):
    return render(request, 'pets/my_pets.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('signup/', signup_page, name='signup_page'),
    path('signin/', signin_page, name='signin_page'),
    path('veterinarians/', veterinarians_page, name='veterinarians_page'),
    path('veterinarians/<uuid:veterinarian_id>/', veterinarian_detail_page, name='veterinarian_detail'),
    path('veterinarians/<uuid:veterinarian_id>/book/', book_appointment_page, name='book_appointment'),
    path('my-pets/', my_pets_page, name='my_pets_page'),
    path('api/signup/', SignupView.as_view(), name='api_signup'),
    path('api/signin/', SigninView.as_view(), name='api_signin'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', UserProfileView.as_view(), name='api_profile'),
    path('api/profile/avatar/upload/', ProfileImageUploadView.as_view(), name='api_avatar_upload'),
    path('api/profile/avatar/delete/', ProfileImageDeleteView.as_view(), name='api_avatar_delete'),
    path('api/profile/vet/avatar/upload/', VeterinarianProfileImageUploadView.as_view(), name='api_vet_avatar_upload'),
    path('api/profile/vet/avatar/delete/', VeterinarianProfileImageDeleteView.as_view(), name='api_vet_avatar_delete'),
    path('api/profile/vet/update/', VeterinarianProfileUpdateView.as_view(), name='api_vet_profile_update'),
    path('api/veterinarians/', VeterinarianListView.as_view(), name='api_veterinarians'),
    path('api/pets/', include('apps.pets.urls')),
    path('veterinarian/complete-profile/', vet_profile_complete_page, name='vet_profile_complete'),
    # Review endpoints
    path('api/veterinarians/<int:veterinarian_id>/reviews/', VeterinarianReviewListCreateView.as_view(), name='api_vet_review_list_create'),
    path('api/reviews/<int:review_id>/', VeterinarianReviewDetailView.as_view(), name='api_vet_review_detail'),
    path('api/reviews/my/', UserReviewListView.as_view(), name='api_my_reviews'),
    path('api/appointments/<int:appointment_id>/review/', AppointmentReviewView.as_view(), name='api_appointment_review'),
    path('api/appointments/available-slots/', AvailableTimeSlotsView.as_view(), name='api_available_slots'),
    path('api/appointments/', AppointmentListCreateView.as_view(), name='api_appointments'),
    # Payment endpoints
    path('api/payments/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='api_create_checkout_session'),
    path('payment/', payment_page, name='payment_page'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),
    path('api/webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
