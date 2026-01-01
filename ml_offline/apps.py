from django.apps import AppConfig


class MlOfflineConfig(AppConfig):
    name = "ml_offline"
    verbose_name = "ai_offline"

    def ready(self):
        # This line is crucial! It connects the Offline events to the Online table.
        pass
