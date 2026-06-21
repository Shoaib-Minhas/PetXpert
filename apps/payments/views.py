import stripe
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.accounts.models import VeterinarianProfile
from .models import Payment, PaymentStatus
from .serializers import PaymentSerializer

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a Stripe Checkout Session for appointment booking
        Redirects to Stripe's hosted checkout page
        """
        try:
            data = json.loads(request.body)
            veterinarian_id = data.get('veterinarian_id')
            pet_id = data.get('pet_id')
            scheduled_at = data.get('scheduled_at')
            duration_minutes = data.get('duration_minutes', 60)
            reason = data.get('reason', '')
            
            # Get veterinarian to get consultation fee
            veterinarian = get_object_or_404(VeterinarianProfile, id=veterinarian_id)
            consultation_fee = float(veterinarian.consultation_fee)
            
            # Calculate tax (example: 5% tax)
            tax_rate = 0.05
            tax_amount = consultation_fee * tax_rate
            total_amount = consultation_fee + tax_amount
            
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'pkr',
                            'product_data': {
                                'name': 'Veterinary Consultation',
                                'description': f'Consultation with Dr. {veterinarian.user.full_name}',
                                'images': [veterinarian.profile_image.url] if veterinarian.profile_image else [],
                            },
                            'unit_amount': int(consultation_fee * 100),  # Stripe uses cents
                        },
                        'quantity': 1,
                    },
                    {
                        'price_data': {
                            'currency': 'pkr',
                            'product_data': {
                                'name': 'Tax',
                                'description': 'Service Tax (5%)',
                            },
                            'unit_amount': int(tax_amount * 100),
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/payment/success/?session_id={CHECKOUT_SESSION_ID}'),
                cancel_url=request.build_absolute_uri('/payment/cancel/'),
                customer_email=request.user.email,
                metadata={
                    'billing_id': f'BILL_{request.user.id}_{veterinarian_id}',
                    'veterinarian_id': str(veterinarian_id),
                    'pet_id': str(pet_id),
                    'scheduled_at': scheduled_at,
                    'duration_minutes': str(duration_minutes),
                    'reason': reason,
                    'user_id': str(request.user.id),
                    'consultation_fee': str(consultation_fee),
                    'tax_amount': str(tax_amount),
                    'total_amount': str(total_amount),
                },
                billing_address_collection='required',
                shipping_address_collection={'allowed_countries': ['PK']},
            )
            
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'consultation_fee': consultation_fee,
                'tax_amount': tax_amount,
                'total_amount': total_amount
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def payment_success(request):
    """
    Display success page after payment completion
    """
    session_id = request.GET.get('session_id')
    context = {
        'session_id': session_id
    }
    return render(request, 'payments/success.html', context)


def payment_cancel(request):
    """
    Display cancel page when user cancels payment
    """
    return render(request, 'payments/cancel.html')


def payment_page(request):
    """
    Render the payment page
    """
    veterinarian_id = request.GET.get('veterinarian_id')
    pet_id = request.GET.get('pet_id')
    scheduled_at = request.GET.get('scheduled_at')
    duration_minutes = request.GET.get('duration_minutes', 60)
    reason = request.GET.get('reason', '')
    
    # Get veterinarian details
    veterinarian = get_object_or_404(VeterinarianProfile, id=veterinarian_id)
    
    # Calculate tax and total
    consultation_fee = float(veterinarian.consultation_fee)
    tax_rate = 0.05
    tax_amount = consultation_fee * tax_rate
    total_amount = consultation_fee + tax_amount
    
    context = {
        'veterinarian': veterinarian,
        'pet_id': pet_id,
        'scheduled_at': scheduled_at,
        'duration_minutes': duration_minutes,
        'reason': reason,
        'consultation_fee': consultation_fee,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    }
    
    return render(request, 'payments/payment.html', context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhooks for checkout session events
    This provides additional security by handling payment events asynchronously
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.id
        
        # Check if payment already processed
        if not Payment.objects.filter(gateway_txn_id=session_id).exists():
            # Get metadata from session
            metadata = session.metadata
            veterinarian_id = metadata.get('veterinarian_id')
            pet_id = metadata.get('pet_id')
            scheduled_at = metadata.get('scheduled_at')
            duration_minutes = int(metadata.get('duration_minutes', 60))
            reason = metadata.get('reason', '')
            user_id = metadata.get('user_id')
            consultation_fee = float(metadata.get('consultation_fee', 0))
            tax_amount = float(metadata.get('tax_amount', 0))
            total_amount = float(metadata.get('total_amount', 0))
            
            # Get user
            from apps.accounts.models import User
            try:
                user = User.objects.get(id=user_id)
                
                # Create appointment
                from apps.appointments.models import Appointment
                from datetime import datetime
                
                appointment = Appointment.objects.create(
                    pet_owner=user,
                    veterinarian_id=veterinarian_id,
                    pet_id=pet_id,
                    scheduled_at=datetime.fromisoformat(scheduled_at),
                    duration_minutes=duration_minutes,
                    fee_charged=consultation_fee,
                    reason=reason,
                    status='CONFIRMED'
                )
                
                # Create payment record
                Payment.objects.create(
                    appointment=appointment,
                    payer=user,
                    amount=total_amount,
                    currency='pkr',
                    status=PaymentStatus.COMPLETED,
                    gateway='Stripe',
                    gateway_txn_id=session_id,
                    paid_at=datetime.now()
                )
                
            except User.DoesNotExist:
                # User not found, log error
                pass
            except Exception as e:
                # Log error for debugging
                pass
    
    return HttpResponse(status=200)
