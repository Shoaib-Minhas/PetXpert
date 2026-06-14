from django.db import models
from apps.core.models import BaseModel
from django.conf import settings
# from django.contrib.postgres.fields import ArrayField

class PetSpecies(models.TextChoices):
    DOG = 'DOG', 'Dog'
    CAT = 'CAT', 'Cat'
    BIRD = 'BIRD', 'Bird'
    RABBIT = 'RABBIT', 'Rabbit'
    FISH = 'FISH', 'Fish'
    REPTILE = 'REPTILE', 'Reptile'
    OTHER = 'OTHER', 'Other'

class PetGender(models.TextChoices):
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    UNKNOWN = 'UNKNOWN', 'Unknown'

class Pet(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='pets', db_index=True)
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=PetSpecies.choices)
    breed = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=PetGender.choices)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    is_neutered = models.BooleanField(default=False)
    microchip_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    blood_type = models.CharField(max_length=10, blank=True, null=True)
    picture = models.ImageField(upload_to='pets/', blank=True, null=True)

    class Meta:
        db_table = 'pets_pet'
