from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"


""" def ready(self):
        # Imports the signals so they are registered when Django starts
        import profiles.signals"""
