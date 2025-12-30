"""
audit_utils.py
Fonctions d'audit pour tracer toutes les actions critiques du système
"""
from django.contrib.auth import get_user_model
from .models import AuditAction  # Modèle doit être dans accounts/models.py

User = get_user_model()

# ============================================================================
# 1. AUDIT DES ÉTUDIANTS
# ============================================================================

def audit_creer_etudiant(request, etudiant_obj):
    """Audit création d'un étudiant"""
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_STUDENT',
        objet=f"Étudiant: {etudiant_obj.matricule}",
        details=f"Matricule: {etudiant_obj.matricule}, "
                f"Nom: {etudiant_obj.user.get_full_name()}, "
                f"Faculté: {etudiant_obj.faculte.nom if etudiant_obj.faculte else 'N/A'}, "
                f"Niveau: {etudiant_obj.get_niveau_display()}, "
                f"Créé par: {request.user.username}",
        faculte=etudiant_obj.faculte.nom if etudiant_obj.faculte else "",
        cours=""  # Pas de cours à la création
    )

def audit_modifier_etudiant(request, etudiant_obj, changements=None):
    """Audit modification d'un étudiant"""
    details = f"Étudiant {etudiant_obj.matricule} modifié"
    if changements:
        details += f". Changements: {changements}"
    
    AuditAction.objects.create(
        user=request.user.username,
        action='UPDATE_STUDENT',
        objet=f"Étudiant: {etudiant_obj.matricule}",
        details=details,
        faculte=etudiant_obj.faculte.nom if etudiant_obj.faculte else "",
        cours=""
    )

def audit_supprimer_etudiant(request, etudiant_obj):
    """Audit suppression d'un étudiant"""
    AuditAction.objects.create(
        user=request.user.username,
        action='DELETE_STUDENT',
        objet=f"Étudiant: {etudiant_obj.matricule}",
        details=f"Matricule: {etudiant_obj.matricule}, "
                f"Nom: {etudiant_obj.user.get_full_name()}, "
                f"Faculté: {etudiant_obj.faculte.nom if etudiant_obj.faculte else 'N/A'}, "
                f"Supprimé définitivement par: {request.user.username}",
        faculte=etudiant_obj.faculte.nom if etudiant_obj.faculte else "",
        cours=""
    )

# ============================================================================
# 2. AUDIT DES PROFESSEURS
# ============================================================================

def audit_creer_professeur(request, professeur_obj):
    """Audit création d'un professeur"""
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_TEACHER',
        objet=f"Professeur: {professeur_obj.user.username}",
        details=f"Nom: {professeur_obj.user.get_full_name()}, "
                f"Spécialité: {professeur_obj.specialite}, "
                f"Statut: {professeur_obj.get_statut_display()}, "
                f"Date embauche: {professeur_obj.date_embauche}, "
                f"Créé par: {request.user.username}",
        faculte="",  # Les profs n'ont pas de faculté directe
        cours=""
    )

def audit_modifier_professeur(request, professeur_obj, changements=None):
    """Audit modification d'un professeur"""
    details = f"Professeur {professeur_obj.user.username} modifié"
    if changements:
        details += f". Changements: {changements}"
    
    AuditAction.objects.create(
        user=request.user.username,
        action='UPDATE_TEACHER',
        objet=f"Professeur: {professeur_obj.user.username}",
        details=details,
        faculte="",
        cours=""
    )

def audit_supprimer_professeur(request, professeur_obj):
    """Audit suppression d'un professeur"""
    AuditAction.objects.create(
        user=request.user.username,
        action='DELETE_TEACHER',
        objet=f"Professeur: {professeur_obj.user.username}",
        details=f"Nom: {professeur_obj.user.get_full_name()}, "
                f"Spécialité: {professeur_obj.specialite}, "
                f"Supprimé définitivement par: {request.user.username}",
        faculte="",
        cours=""
    )

# ============================================================================
# 3. AUDIT DES ADMINISTRATEURS
# ============================================================================

def audit_creer_admin(request, admin_obj):
    """Audit création d'un administrateur"""
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_ADMIN',
        objet=f"Admin: {admin_obj.user.username}",
        details=f"Nom: {admin_obj.user.get_full_name()}, "
                f"Niveau accès: {admin_obj.get_niveau_acces_display()}, "
                f"Permissions: Gestion utilisateurs={admin_obj.peut_gerer_utilisateurs}, "
                f"Gestion cours={admin_obj.peut_gerer_cours}, "
                f"Validation notes={admin_obj.peut_valider_notes}, "
                f"Gestion facultés={admin_obj.peut_gerer_facultes}, "
                f"Créé par: {request.user.username}",
        faculte="",
        cours=""
    )

# ============================================================================
# 4. AUDIT DES COURS (academics)
# ============================================================================

def audit_creer_cours(request, cours_obj):
    """Audit création d'un cours"""
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_COURSE',
        objet=f"Cours: {cours_obj.code}",
        details=f"Code: {cours_obj.code}, "
                f"Intitulé: {cours_obj.intitule}, "
                f"Faculté: {cours_obj.faculte.nom}, "
                f"Niveau: {cours_obj.get_niveau_display()}, "
                f"Semestre: {cours_obj.get_semestre_display()}, "
                f"Crédits: {cours_obj.credits}, "
                f"Professeur: {cours_obj.professeur.get_full_name() if cours_obj.professeur else 'Non assigné'}",
        faculte=cours_obj.faculte.nom,
        cours=cours_obj.code
    )

def audit_modifier_cours(request, cours_obj, changements=None):
    """Audit modification d'un cours"""
    details = f"Cours {cours_obj.code} modifié"
    if changements:
        details += f". Changements: {changements}"
    
    AuditAction.objects.create(
        user=request.user.username,
        action='UPDATE_COURSE',
        objet=f"Cours: {cours_obj.code}",
        details=details,
        faculte=cours_obj.faculte.nom if cours_obj.faculte else "",
        cours=cours_obj.code
    )

def audit_supprimer_cours(request, cours_obj):
    """Audit suppression d'un cours"""
    AuditAction.objects.create(
        user=request.user.username,
        action='DELETE_COURSE',
        objet=f"Cours: {cours_obj.code} - {cours_obj.intitule}",
        details=f"Supprimé définitivement. "
                f"Code: {cours_obj.code}, "
                f"Faculté: {cours_obj.faculte.nom}, "
                f"Professeur: {cours_obj.professeur.get_full_name() if cours_obj.professeur else 'Aucun'}",
        faculte=cours_obj.faculte.nom,
        cours=cours_obj.code
    )

# ============================================================================
# 5. AUDIT DES FACULTÉS
# ============================================================================

def audit_creer_faculte(request, faculte_obj):
    """Audit création d'une faculté"""
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_FACULTY',
        objet=f"Faculté: {faculte_obj.code}",
        details=f"Code: {faculte_obj.code}, "
                f"Nom: {faculte_obj.nom}, "
                f"Description: {faculte_obj.description[:100]}...",
        faculte=faculte_obj.nom,
        cours=""
    )

def audit_supprimer_faculte(request, faculte_obj):
    """Audit suppression d'une faculté"""
    # Compter combien de cours seront affectés
    cours_count = faculte_obj.cours_set.count()
    
    AuditAction.objects.create(
        user=request.user.username,
        action='DELETE_FACULTY',
        objet=f"Faculté: {faculte_obj.nom}",
        details=f"Supprimée. "
                f"Code: {faculte_obj.code}, "
                f"Affecte {cours_count} cours(s). "
                f"Supprimée par: {request.user.username}",
        faculte=faculte_obj.nom,
        cours=""
    )

# ============================================================================
# 6. AUDIT DES ANNONCES
# ============================================================================

def audit_creer_annonce(request, annonce_obj):
    """Audit création d'une annonce"""
    destinataires = []
    if annonce_obj.destinataire_tous: destinataires.append("Tous")
    if annonce_obj.destinataire_etudiants: destinataires.append("Étudiants")
    if annonce_obj.destinataire_professeurs: destinataires.append("Professeurs")
    if annonce_obj.destinataire_admins: destinataires.append("Admins")
    
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_ANNOUNCE',
        objet=f"Annonce: {annonce_obj.titre}",
        details=f"Titre: {annonce_obj.titre}, "
                f"Type: {annonce_obj.get_type_annonce_display()}, "
                f"Priorité: {annonce_obj.get_priorite_display()}, "
                f"Destinataires: {', '.join(destinataires)}, "
                f"Faculté: {annonce_obj.faculte.nom if annonce_obj.faculte else 'Toutes'}, "
                f"Auteur: {annonce_obj.auteur.get_full_name() if annonce_obj.auteur else 'N/A'}",
        faculte=annonce_obj.faculte.nom if annonce_obj.faculte else "",
        cours=""
    )

def audit_supprimer_annonce(request, annonce_obj):
    """Audit suppression d'une annonce"""
    AuditAction.objects.create(
        user=request.user.username,
        action='DELETE_ANNOUNCE',
        objet=f"Annonce: {annonce_obj.titre}",
        details=f"Type: {annonce_obj.get_type_annonce_display()}, "
                f"Publiée le: {annonce_obj.date_publication.strftime('%d/%m/%Y')}, "
                f"Supprimée par: {request.user.username}",
        faculte=annonce_obj.faculte.nom if annonce_obj.faculte else "",
        cours=""
    )

# ============================================================================
# 7. AUDIT DES NOTES (grades)
# ============================================================================

def audit_saisir_notes(request, cours_obj, nb_notes):
    """Audit saisie de notes par un professeur"""
    AuditAction.objects.create(
        user=request.user.username,
        action='CREATE_GRADES',
        objet=f"Cours: {cours_obj.code}",
        details=f"Professeur {request.user.username} a saisi {nb_notes} note(s) pour le cours {cours_obj.code}. "
                f"Statut: brouillon",
        faculte=cours_obj.faculte.nom if cours_obj.faculte else "",
        cours=cours_obj.code
    )

def audit_soumettre_notes(request, cours_obj, nb_notes):
    """Audit soumission de notes pour validation"""
    AuditAction.objects.create(
        user=request.user.username,
        action='SUBMIT_GRADES',
        objet=f"Cours: {cours_obj.code}",
        details=f"Professeur {request.user.username} a soumis {nb_notes} note(s) pour validation. "
                f"Cours: {cours_obj.intitule}, "
                f"Statut: soumis pour validation",
        faculte=cours_obj.faculte.nom if cours_obj.faculte else "",
        cours=cours_obj.code
    )

def audit_publier_notes(request, cours_obj, nb_notes, admin_user):
    """Audit publication de notes par un admin"""
    AuditAction.objects.create(
        user=admin_user.username if admin_user else request.user.username,
        action='PUBLISH_GRADES',
        objet=f"Cours: {cours_obj.code}",
        details=f"Admin {admin_user.username if admin_user else request.user.username} a publié {nb_notes} note(s). "
                f"Cours: {cours_obj.intitule}, "
                f"Statut: publié (visible étudiants)",
        faculte=cours_obj.faculte.nom if cours_obj.faculte else "",
        cours=cours_obj.code
    )

def audit_rejeter_notes(request, cours_obj, nb_notes, motif):
    """Audit rejet de notes par un admin"""
    AuditAction.objects.create(
        user=request.user.username,
        action='REJECT_GRADES',
        objet=f"Cours: {cours_obj.code}",
        details=f"Admin {request.user.username} a rejeté {nb_notes} note(s). "
                f"Cours: {cours_obj.intitule}, "
                f"Motif: {motif}, "
                f"Statut: rejeté",
        faculte=cours_obj.faculte.nom if cours_obj.faculte else "",
        cours=cours_obj.code
    )

# ============================================================================
# 8. AUDIT DES CONNEXIONS/DÉCONNEXIONS
# ============================================================================

# def audit_login(request, user):
#     """Audit connexion d'un utilisateur"""
#     AuditAction.objects.create(
#         user=user.username,
#         action='USER_LOGIN',
#         objet=f"Utilisateur: {user.username}",
#         details=f"Connexion réussie. "
#                 f"Rôle: {user.get_role_display() if hasattr(user, 'get_role_display') else 'N/A'}, "
#                 f"IP: {request.META.get('REMOTE_ADDR', 'N/A')}, "
#                 f"Date: {request.user.last_login.strftime('%d/%m/%Y %H:%M') if request.user.last_login else 'N/A'}",
#         faculte="",
#         cours=""
#     )
def audit_login(request, user):
    """Audit connexion d'un utilisateur - CORRIGÉ POUR HAÏTI"""
    from django.utils import timezone
    
    # CORRECTION : Utiliser l'heure locale, pas last_login (qui est en UTC)
    local_time = timezone.localtime(timezone.now())
    
    # CORRECTION : Meilleure récupération d'IP
    ip_address = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or
        request.META.get('HTTP_X_REAL_IP', '') or
        request.META.get('REMOTE_ADDR', 'N/A')
    )
    
    AuditAction.objects.create(
        user=user.username,
        action='USER_LOGIN',
        objet=f"Utilisateur: {user.username}",
        details=(
            f"Connexion réussie. "
            f"Rôle: {user.get_role_display() if hasattr(user, 'get_role_display') else 'N/A'}, "
            f"IP: {ip_address}, "
            f"Heure (Haïti): {local_time.strftime('%d/%m/%Y %H:%M')}"  # ← CORRIGÉ
        ),
        faculte="",
        cours=""
    )

def audit_logout(request, user):
    """Audit déconnexion d'un utilisateur"""
    AuditAction.objects.create(
        user=user.username,
        action='USER_LOGOUT',
        objet=f"Utilisateur: {user.username}",
        details=f"Déconnexion. Session terminée.",
        faculte="",
        cours=""
    )

def audit_login_failed(request, username):
    """Audit tentative de connexion échouée"""
    AuditAction.objects.create(
        user="SYSTEM",  # Pas d'utilisateur authentifié
        action='LOGIN_FAILED',
        objet=f"Tentative: {username}",
        details=f"Tentative de connexion échouée. "
                f"Nom d'utilisateur: {username}, "
                f"IP: {request.META.get('REMOTE_ADDR', 'N/A')}, "
                f"Raison: Mot de passe incorrect ou compte non trouvé",
        faculte="",
        cours=""
    )

# ============================================================================
# 9. FONCTION GÉNÉRIQUE
# ============================================================================

def audit_action_generique(request, action_code, objet, details="", faculte="", cours=""):
    """
    Fonction générique pour les actions non couvertes par les fonctions spécifiques
    
    Utilisation:
    audit_action_generique(request, 'EXPORT_DATA', 'Export étudiants', 
                          'Export CSV des étudiants par l\'admin X')
    """
    AuditAction.objects.create(
        user=request.user.username if request.user.is_authenticated else "ANONYMOUS",
        action=action_code,
        objet=objet[:100],
        details=details[:500],
        faculte=faculte[:100],
        cours=cours[:100]
    )
