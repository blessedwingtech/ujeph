# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Admin, User, Etudiant, Professeur
from academics.models import Faculte

# --------------------------------------------------------------------
# ✅ 1. Création automatique du profil (Étudiant, Professeur ou Admin)
# --------------------------------------------------------------------
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """
#     Crée automatiquement un profil quand un User est créé avec un rôle.
#     """
#     if created and instance.role:
#         print(f"🔄 Signal déclenché pour {instance.username} (rôle: {instance.role})")

#         # === Étudiant ===
#         if instance.role == User.Role.ETUDIANT:
#             create_etudiant_profile(instance)
        
#         # === Professeur ===
#         elif instance.role == User.Role.PROFESSEUR:
#             create_professeur_profile(instance)
        
#         # === Admin ===
#         elif instance.role == User.Role.ADMIN:
#             create_admin_profile(instance)

# Dans signals.py - Modifier la fonction
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil quand un User est créé avec un rôle.
    MAIS seulement si le profil n'existe pas déjà
    """
    # ⚠️ AJOUTER CETTE VÉRIFICATION !
    if hasattr(instance, '_profile_created_manually'):
        print(f"⏭️ Signal sauté pour {instance.username} (_profile_created_manually=True)")
        return
    
    if created and instance.role:
        print(f"🔄 Signal déclenché pour {instance.username} (rôle: {instance.role})")

        # Vérifier si un profil existe déjà
        if instance.role == User.Role.ETUDIANT and not hasattr(instance, 'etudiant'):
            create_etudiant_profile(instance)
        elif instance.role == User.Role.PROFESSEUR and not hasattr(instance, 'professeur'):
            create_professeur_profile(instance)
        elif instance.role == User.Role.ADMIN and not hasattr(instance, 'admin'):
            create_admin_profile(instance)
            

def create_etudiant_profile(user_instance):
    """Crée un profil étudiant avec valeurs par défaut"""
    try:
        if not hasattr(user_instance, 'etudiant'):
            # Trouver ou créer une faculté par défaut
            faculte_default, _ = Faculte.objects.get_or_create(
                code='DEFAULT',
                defaults={
                    'nom': 'Faculté par défaut',
                    'description': "Faculté temporaire en attente d'affectation"
                }
            )

            matricule = f"ETU-{user_instance.id:04d}"

            etudiant = Etudiant.objects.create(
                user=user_instance,
                matricule=matricule,
                faculte=faculte_default,
                niveau='1ere',
                adresse='À renseigner',
                date_naissance='2000-01-01',
                sexe='M'
            )
            print(f"✅ Profil Étudiant créé pour {user_instance.username}")
            
            # Déclencher l'attribution des cours
            assigner_cours_automatiquement(etudiant)
            
    except Exception as e:
        print(f"❌ Erreur création profil étudiant: {e}")

def create_professeur_profile(user_instance):
    """Crée un profil professeur avec valeurs par défaut"""
    try:
        if not hasattr(user_instance, 'professeur'):
            Professeur.objects.create(
                user=user_instance,
                specialite="À renseigner",
                date_embauche=timezone.now().date(),
                statut="Permanent"
            )
            print(f"✅ Profil Professeur créé pour {user_instance.username}")
    except Exception as e:
        print(f"❌ Erreur création profil professeur: {e}")

def create_admin_profile(user_instance):
    """Crée un profil admin avec valeurs par défaut"""
    try:
        if not hasattr(user_instance, 'admin'):
            Admin.objects.create(
                user=user_instance,
                niveau_acces='utilisateurs'
            )
            print(f"✅ Profil Admin créé pour {user_instance.username}")
    except Exception as e:
        print(f"❌ Erreur création profil admin: {e}")

# --------------------------------------------------------------------
# ✅ 2. Attribution automatique des cours à un étudiant nouvellement créé
# --------------------------------------------------------------------
def assigner_cours_automatiquement(etudiant_instance):
    """Attribue automatiquement les cours correspondant à la faculté et au niveau de l'étudiant."""
    try:
        from grades.models import InscriptionCours
        from academics.models import Cours
        
        # ✅ CORRECTION : DÉTERMINER LE SEMESTRE
        # mois = timezone.now().month
        # semestre = 'S1' if (9 <= mois <= 12 or mois == 1) else 'S2'
        semestre = etudiant_instance.semestre_courant
        # ✅ CORRECTION : FILTRER PAR SEMESTRE
        cours_disponibles = Cours.objects.filter(
            faculte=etudiant_instance.faculte,
            niveau=etudiant_instance.niveau,
            semestre=semestre  # ← AJOUTER CETTE LIGNE
        )
        
        for cours in cours_disponibles:
            InscriptionCours.objects.get_or_create(
                etudiant=etudiant_instance, 
                cours=cours
            )
            
        print(f"📚 {cours_disponibles.count()} cours attribués à {etudiant_instance.matricule}")
        
    except Exception as e:
        print(f"⚠️ Erreur d'attribution automatique des cours : {e}")

# Signal séparé pour les étudiants créés manuellement
@receiver(post_save, sender=Etudiant)
def on_etudiant_created(sender, instance, created, **kwargs):
    """Quand un étudiant est créé manuellement dans l'admin"""
    if created:
        assigner_cours_automatiquement(instance)




# Dans signals.py - Ajouter à la fin
@receiver(post_save, sender=Professeur)
@receiver(post_save, sender=Etudiant) 
@receiver(post_save, sender=Admin)
def update_user_role_on_profile_creation(sender, instance, created, **kwargs):
    """Met à jour le rôle du User quand un profil est créé"""
    if created:
        role_mapping = {
            Professeur: User.Role.PROFESSEUR,
            Etudiant: User.Role.ETUDIANT, 
            Admin: User.Role.ADMIN
        }
        
        expected_role = role_mapping.get(sender)
        if expected_role and instance.user.role != expected_role:
            instance.user.role = expected_role
            instance.user.save()
            print(f"✅ Rôle mis à jour pour {instance.user.username} -> {expected_role}")


