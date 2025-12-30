# grades/apps.py
from django.apps import AppConfig


class GradesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grades'
    
    def ready(self):
        # Importez les signaux ici pour qu'ils soient chargés
        import grades.signals
        print("✅ Signaux de grades chargés")