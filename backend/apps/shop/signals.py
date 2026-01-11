from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from backend.apps.shop.models import Review
from backend.apps.shop.tasks import calculate_average_rating


@receiver(post_save, sender=Review)
def calculate_avg_rating_on_save(sender, instance, **kwargs):
    calculate_average_rating.delay(instance.id)


@receiver(post_delete, sender=Review)
def calculate_avg_rating_on_delete(sender, instance, **kwargs):
    calculate_average_rating.delay(instance.id)
