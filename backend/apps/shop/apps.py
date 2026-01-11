from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.shop"

    def ready(self):
        import backend.apps.shop.signals  # noqa
