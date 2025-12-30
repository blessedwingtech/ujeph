from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Etudiant

@receiver(post_save, sender=Etudiant)
def verifier_cours_etudiant(sender, instance, created, **kwargs):
    """
    Vérifie que l'étudiant a des cours correspondant à sa faculté/niveau
    (Logique métier SEL EF-006)
    """
    if created:
        from .models import Cours  # ✅ SEULEMENT Cours
        cours_correspondants = Cours.objects.filter(
            faculte=instance.faculte,
            niveau=instance.niveau
        )
        
        if cours_correspondants.exists():
            print(f"✅ Étudiant {instance} peut avoir des notes dans {cours_correspondants.count()} cours")
        else:
            print(f"⚠️ Aucun cours trouvé pour {instance.faculte.nom} - Niveau {instance.niveau}")