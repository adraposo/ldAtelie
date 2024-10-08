from django.apps import AppConfig


class LojaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loja"

    # def ready(self):

    #     from .models import User
    #     import os

    #     email = os.getenv("EMAIL_ADMIN")
    #     senha = os.getenv("SENHA_ADMIN")

    #     users = User.objects.filter(email=email)
    #     print(users)
    #     if not users:
    #         User.objects.create_superuser(username="admin01", email=email, password=senha,
    #                                          is_active=True, is_staff=True)
            

