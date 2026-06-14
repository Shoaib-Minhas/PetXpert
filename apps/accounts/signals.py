from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import VeterinarianReview, VeterinarianProfile


@receiver(post_save, sender=VeterinarianReview)
def update_veterinarian_rating_on_save(sender, instance, created, **kwargs):
    """
    Automatically recalculate avg_rating and rating_count when a review is created or updated.
    """
    veterinarian = instance.veterinarian
    reviews = VeterinarianReview.objects.filter(veterinarian=veterinarian)
    
    if reviews.exists():
        veterinarian.avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        veterinarian.rating_count = reviews.count()
    else:
        veterinarian.avg_rating = 0
        veterinarian.rating_count = 0
    
    veterinarian.save(update_fields=['avg_rating', 'rating_count'])


@receiver(post_delete, sender=VeterinarianReview)
def update_veterinarian_rating_on_delete(sender, instance, **kwargs):
    """
    Automatically recalculate avg_rating and rating_count when a review is deleted.
    """
    veterinarian = instance.veterinarian
    reviews = VeterinarianReview.objects.filter(veterinarian=veterinarian)
    
    if reviews.exists():
        veterinarian.avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        veterinarian.rating_count = reviews.count()
    else:
        veterinarian.avg_rating = 0
        veterinarian.rating_count = 0
    
    veterinarian.save(update_fields=['avg_rating', 'rating_count'])
