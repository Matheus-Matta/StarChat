from django.apps import AppConfig


class StarchatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'starchat'

    def ready(self):
        import starchat.signals  # Importa os sinais para sincronização com Chatwoot