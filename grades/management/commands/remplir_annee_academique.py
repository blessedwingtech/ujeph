# grades/management/commands/remplir_annee_academique.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from grades.models import Note

class Command(BaseCommand):
    help = 'Remplit le champ annee_academique pour les notes existantes'

    def handle(self, *args, **kwargs):
        notes = Note.objects.filter(annee_academique__isnull=True)
        
        for note in notes:
            if note.date_validation:
                annee = note.date_validation.year
                note.annee_academique = f"{annee}-{annee+1}"
            else:
                # Si pas de date de validation, utiliser l'année actuelle
                annee = timezone.now().year
                note.annee_academique = f"{annee}-{annee+1}"
            
            note.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ {notes.count()} notes mises à jour avec année académique')
        )