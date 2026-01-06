from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError


class CustomUserManager(BaseUserManager):

    def email_validator(self, email: str):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Email address is invalid")

    def validate_user(self, first_name, last_name, email, password):
        if not first_name:
            raise ValueError("Users must submit a first name")

        if not last_name:
            raise ValueError("Users must submit a last name")

        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError("Base User Account: An email address is required")

        if not password:
            raise ValueError("User must have a password")

    def create_user(self, first_name, last_name, email, password, **extra_fields):
        self.validate_user(first_name, last_name, email, password)

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            **extra_fields
        )

        user.set_password(password)
        user.save()
        return user

    def validate_superuser(self, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        return extra_fields

    def create_superuser(self, first_name, last_name, email, password, **extra_fields):
        extra_fields = self.validate_superuser(**extra_fields)
        user = self.create_user(first_name, last_name, email, password, **extra_fields)
        return user
