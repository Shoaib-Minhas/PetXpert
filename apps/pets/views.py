from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Pet
from .serializers import PetSerializer


@method_decorator(csrf_exempt, name='dispatch')
class PetListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        """
        List all pets for the current user.
        """
        try:
            pets = Pet.objects.filter(owner=request.user)
            serializer = PetSerializer(pets, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Create a new pet for the current user.
        """
        try:
            serializer = PetSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class PetDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request, pet_id):
        """
        Get a specific pet.
        """
        try:
            pet = Pet.objects.get(id=pet_id, owner=request.user)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PetSerializer(pet)
        return Response(serializer.data)

    def put(self, request, pet_id):
        """
        Update a pet.
        """
        try:
            pet = Pet.objects.get(id=pet_id, owner=request.user)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            serializer = PetSerializer(pet, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pet_id):
        """
        Delete a pet.
        """
        try:
            pet = Pet.objects.get(id=pet_id, owner=request.user)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        
        pet.delete()
        return Response({'message': 'Pet deleted successfully'}, status=status.HTTP_200_OK)
