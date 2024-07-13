import uuid
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models


class CustomUserManager(BaseUserManager):

    def create_superuser(self, cpf, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser has to have is_staff being True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser has to have is_superuser being True")

        return self.create_user(cpf=cpf, password=password, **extra_fields)

    def create_user(self, password, cpf, **extra_fields):
        user = self.model(cpf=cpf, **extra_fields)
        user.set_password(password)
        user.save()
        return user


class UserType:
    COMUM = "COMUM"
    ADMIN = "ADMIN"

    TYPES = (
        (COMUM, "Comum"),
        (ADMIN, "Admin"),
    )


class Usuario(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpf = models.IntegerField(unique=True, validators=[MaxValueValidator(99999999999)])
    email = models.EmailField(unique=True, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=UserType.TYPES, null=True, blank=True)
    is_primeiro_acesso = models.BooleanField(default=True)
    USERNAME_FIELD = "cpf"
    username = None

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.cpf} - {self.email}'


class Ingresso(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="ingressos")

    created_at = models.DateTimeField(auto_now_add=True)
    utilizado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.usuario} - {self.created_at}'
