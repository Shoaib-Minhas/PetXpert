from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import datetime, time
from .models import Appointment
from .serializers import AppointmentSerializer


@method_decorator(csrf_exempt, name='dispatch')
class AvailableTimeSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get available time slots for a veterinarian on a specific date.
        Slots are from 9:00-13:00 and 14:00-16:00 in 1-hour intervals.
        Excludes slots with PENDING or CONFIRMED appointments.
        """
        veterinarian_id = request.GET.get('veterinarian_id')
        date_str = request.GET.get('date')
        
        if not veterinarian_id or not date_str:
            return Response(
                {'error': 'veterinarian_id and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Parse the date
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Define time ranges: 9:00-13:00 and 14:00-16:00
            morning_slots = self._generate_time_slots(time(9, 0), time(13, 0))
            afternoon_slots = self._generate_time_slots(time(14, 0), time(16, 0))
            all_slots = morning_slots + afternoon_slots
            
            # Fetch existing appointments for this veterinarian on this date
            # Exclude COMPLETED appointments (they should unlock the slot)
            existing_appointments = Appointment.objects.filter(
                veterinarian_id=veterinarian_id,
                scheduled_at__date=selected_date,
                status__in=['PENDING', 'CONFIRMED']
            )
            
            # Get booked time slots
            booked_times = set()
            for appointment in existing_appointments:
                appointment_time = appointment.scheduled_at.time()
                # Round to nearest hour
                booked_time = time(appointment_time.hour, 0)
                booked_times.add(booked_time.strftime('%H:%M'))
            
            # Mark slots as available or booked
            available_slots = []
            for slot_time in all_slots:
                is_available = slot_time not in booked_times
                
                # Convert to display format
                hour = int(slot_time.split(':')[0])
                minute = int(slot_time.split(':')[1])
                if hour >= 12:
                    display_hour = hour - 12 if hour > 12 else 12
                    display_time = f"{display_hour}:{minute:02d} PM"
                else:
                    display_time = f"{hour}:{minute:02d} AM"
                
                available_slots.append({
                    'time': slot_time,
                    'display': display_time,
                    'available': is_available
                })
            
            return Response(available_slots)
            
        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_time_slots(self, start_time, end_time):
        """Generate 1-hour time slots between start and end time."""
        slots = []
        current = start_time
        while current < end_time:
            slots.append(current.strftime('%H:%M'))
            # Add 1 hour
            current = time(current.hour + 1, 0)
        return slots


@method_decorator(csrf_exempt, name='dispatch')
class AppointmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List all appointments for the current user.
        """
        try:
            appointments = Appointment.objects.filter(pet_owner=request.user)
            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Create a new appointment.
        """
        try:
            serializer = AppointmentSerializer(data=request.data)
            if serializer.is_valid():
                # Set the pet_owner to the current user
                serializer.save(pet_owner=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
