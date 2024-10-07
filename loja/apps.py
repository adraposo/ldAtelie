from django.apps import AppConfig


class LojaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loja"

    def ready(self):
        from .models import Cliente
        import os

        email = os.getenv("EMAIL_ADMIN")
        senha = os.getenv("SENHA_ADMIN")

        cliente = Cliente.objects.filter(email=email)

        if not cliente:
            Cliente.objects.create_superuser(username="admin", email=email, password=senha,
                                             is_active=True, is_staff=True)
            

