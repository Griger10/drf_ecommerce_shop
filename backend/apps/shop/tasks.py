from django.db.models import Avg
from celery import shared_task

from backend.apps.shop.models import Product


@shared_task
def calculate_average_rating(product_id: int) -> float:
    product = Product.objects.get(pk=product_id)
    result = product.reviews.aggregate(avg=Avg("rating"))
    rating = result.get("avg", 0.0)
    product.average_rating = rating
    product.save(update_fields=["average_rating"])
    return rating
