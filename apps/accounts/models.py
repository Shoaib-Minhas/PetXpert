from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.core.models import BaseModel

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class UserRole(models.TextChoices):
    PET_OWNER = 'PET_OWNER', 'Pet Owner'
    VETERINARIAN = 'VETERINARIAN', 'Veterinarian'
    ADMIN = 'ADMIN', 'Admin'

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to='avatars/users/', null=True, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PET_OWNER, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users_user'

class VeterinarianStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    VERIFIED = 'VERIFIED', 'Verified'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    REJECTED = 'REJECTED', 'Rejected'

class VeterinarianProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vet_profile')
    profile_image = models.ImageField(upload_to='avatars/vets/', null=True, blank=True)
    license_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=VeterinarianStatus.choices, default=VeterinarianStatus.PENDING, db_index=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bio = models.TextField(max_length=1000, blank=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, db_index=True)
    rating_count = models.IntegerField(default=0, db_index=True)
    total_consultations = models.IntegerField(default=0)
    location = models.CharField(max_length=255, blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    clinic_name = models.CharField(max_length=255, blank=True, null=True)
    clinic_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'users_veterinarianprofile'

class VeterinarianReview(BaseModel):
    veterinarian = models.ForeignKey(VeterinarianProfile, on_delete=models.RESTRICT, related_name='reviews', db_index=True)
    patient = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='vet_reviews', db_index=True)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.RESTRICT, related_name='review', db_index=True)
    rating = models.PositiveSmallIntegerField(db_index=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'users_veterinarianreview'
        unique_together = [['patient', 'appointment']]
        constraints = [
            models.CheckConstraint(condition=models.Q(rating__gte=1) & models.Q(rating__lte=5), name='chk_rating_range')
        ]
        ordering = ['-created_at']
