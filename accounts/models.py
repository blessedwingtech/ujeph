from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        AUCUN = "", _("Aucun rôle")  # ✅ Ajout d'un choix vide
        ADMIN = "admin", _("Administrateur")
        PROFESSEUR = "prof", _("Professeur")
        ETUDIANT = "student", _("Étudiant")

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.AUCUN,  # ✅ Rôle vide par défaut
        blank=True
    )
    telephone = models.CharField(max_length=20, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    first_login = models.BooleanField(default=True)

    def set_password(self, raw_password):
        super().set_password(raw_password)
        # Quand l'admin change le mot de passe, on marque first_login=True
        if self.pk and hasattr(self, '_password_changed_by_admin'):
            self.first_login = True
            self.save()


    def __str__(self):
        if self.role:
            return f"{self.username} ({self.get_role_display()})"
        return f"{self.username} (Aucun rôle)"  # ✅ Affichage si rôle vide


class Professeur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialite = models.CharField(max_length=100)
    date_embauche = models.DateField()
    statut = models.CharField(max_length=20, choices=[('Permanent', 'Permanent'), ('Vacataire', 'Vacataire')])

    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"

def get_annee_academique():
    """Retourne l'année académique courante"""
    now = timezone.now()
    return f"{now.year}-{now.year+1}"

class Etudiant(models.Model):
    # CORRECTION : Ajout des choix pour le niveau
    NIVEAU_CHOICES = [
        ('1ere', '1ère année'),
        ('2e', '2e année'), 
        ('3e', '3e année'),
        ('4e', '4e année'),
        ('5e', '5e année'),
    ]

    SEMESTRE_CHOICES = [
        ('S1', 'Semestre 1 (Sept-Jan)'),
        ('S2', 'Semestre 2 (Fév-Juin)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricule = models.CharField(max_length=20, unique=True)
    faculte = models.ForeignKey('academics.Faculte', on_delete=models.CASCADE)
    # CORRECTION : Utilisation des choix pour le niveau
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, default='1ere')
    # ✅ NOUVEAU CHAMP
    semestre_courant = models.CharField(
        max_length=10, 
        choices=SEMESTRE_CHOICES, 
        default='S1'
    )
    date_inscription = models.DateField(auto_now_add=True)
    adresse = models.CharField(max_length=200)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    telephone_parent = models.CharField(max_length=20, blank=True, null=True)

     # ✅ AJOUTER CES 3 CHAMPS À LA FIN de la classe :
    annee_academique_courante = models.CharField(
        max_length=9,
        default=get_annee_academique,  # ✅ Fonction appelée à chaque création
        verbose_name="Année académique"
    )
    
    statut_academique = models.CharField(
        max_length=20,
        choices=[
            ('actif', 'Actif'),
            ('redoublant', 'Redoublant'),
            ('diplome', 'Diplômé'),
            ('abandon', 'Abandon'),
        ],
        default='actif',
        verbose_name="Statut académique"
    )
    
    moyenne_generale = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Moyenne générale"
    )
    
    # ✅ AJOUTER CETTE MÉTHODE À LA CLASSE :
    def calculer_moyenne_generale(self):
        """Calcule la moyenne générale (S1 + S2) / 2"""
        from grades.models import MoyenneSemestre
        from django.utils import timezone
        
        annee_courante = f"{timezone.now().year}-{timezone.now().year+1}"
        
        # Récupérer les moyennes stockées
        moyenne_s1 = MoyenneSemestre.objects.filter(
            etudiant=self,
            semestre='S1',
            annee_academique=annee_courante
        ).first()
        
        moyenne_s2 = MoyenneSemestre.objects.filter(
            etudiant=self,
            semestre='S2',
            annee_academique=annee_courante
        ).first()
        
        # Calculer la moyenne générale
        if moyenne_s1 and moyenne_s2:
            return (float(moyenne_s1.moyenne) + float(moyenne_s2.moyenne)) / 2
        elif moyenne_s2:
            return float(moyenne_s2.moyenne)
        elif moyenne_s1:
            return float(moyenne_s1.moyenne)
        else:
            return None

    def __str__(self):
        return f"{self.matricule} - {self.user.get_full_name()}"
    
    
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_nomination = models.DateField(auto_now_add=True)
    niveau_acces = models.CharField(
        max_length=20,
        choices=[
            ('super', 'Super Administrateur'),
            ('academique', 'Administrateur Académique'),
            ('utilisateurs', 'Gestionnaire Utilisateurs')
        ],
        default='utilisateurs'
    )
    # Permissions granulaires
    peut_gerer_utilisateurs = models.BooleanField(default=True)
    peut_gerer_cours = models.BooleanField(default=True)
    peut_valider_notes = models.BooleanField(default=True)
    peut_gerer_facultes = models.BooleanField(default=True)
    
    def has_perm(self, permission_code):
        permissions = {
            'users.create': self.peut_gerer_utilisateurs,
            'users.delete': self.peut_gerer_utilisateurs,
            'courses.manage': self.peut_gerer_cours,
            'grades.validate': self.peut_valider_notes,
            'faculties.manage': self.peut_gerer_facultes,
        }
        return permissions.get(permission_code, False)
    
    
    def __str__(self):
        return f"Admin {self.user.get_full_name()}"




# accounts/models.py - AJOUTEZ à la fin du fichier
#model pour audit
# À la fin de accounts/models.py, ajoutez :

class AuditAction(models.Model):
    """Modèle pour tracer toutes les actions critiques du système"""
    
    ACTIONS = [
        # Utilisateurs
        ('CREATE_STUDENT', 'Création étudiant'),
        ('UPDATE_STUDENT', 'Modification étudiant'),
        ('DELETE_STUDENT', 'Suppression étudiant'),
        ('CREATE_TEACHER', 'Création professeur'),
        ('UPDATE_TEACHER', 'Modification professeur'),
        ('DELETE_TEACHER', 'Suppression professeur'),
        ('CREATE_ADMIN', 'Création administrateur'),
        ('USER_LOGIN', 'Connexion utilisateur'),
        ('USER_LOGOUT', 'Déconnexion utilisateur'),
        ('LOGIN_FAILED', 'Connexion échouée'),
        
        # Academics
        ('CREATE_COURSE', 'Création cours'),
        ('UPDATE_COURSE', 'Modification cours'),
        ('DELETE_COURSE', 'Suppression cours'),
        ('CREATE_FACULTY', 'Création faculté'),
        ('DELETE_FACULTY', 'Suppression faculté'),
        ('CREATE_ANNOUNCE', 'Création annonce'),
        ('DELETE_ANNOUNCE', 'Suppression annonce'),
        
        # Notes
        ('CREATE_GRADES', 'Saisie notes (brouillon)'),
        ('SUBMIT_GRADES', 'Soumission notes'),
        ('PUBLISH_GRADES', 'Publication notes'),
        ('REJECT_GRADES', 'Rejet notes'),
        ('RESET_GRADES', 'Remise en brouillon'),
        
        # Autres
        ('EXPORT_DATA', 'Export données'),
        ('CREATE_STUDENT_FAILED', 'Échec création étudiant'),
        ('CREATE_TEACHER_FAILED', 'Échec création professeur'),
        ('CREATE_ADMIN_FAILED', 'Échec création admin'),
    ]
    
    # Champs essentiels
    user = models.CharField(max_length=150)  # Nom d'utilisateur
    action = models.CharField(max_length=50, choices=ACTIONS)
    objet = models.CharField(max_length=100)  # "Étudiant: MAT2024001", "Cours: MAT101"
    details = models.TextField(blank=True)    # Détails spécifiques
    date = models.DateTimeField(auto_now_add=True)
    
    # Contexte académique (pour filtrage facile)
    faculte = models.CharField(max_length=100, blank=True)
    cours = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['faculte']),
        ]
        verbose_name = "Action d'audit"
        verbose_name_plural = "Actions d'audit"
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.objet}"
    


class LoginAttempt(models.Model):
    """Modèle pour tracker les tentatives de connexion"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False) 
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        verbose_name = "Tentative de connexion"
        verbose_name_plural = "Tentatives de connexion"
    
    def __str__(self):
        status = "Succès" if self.successful else "Échec"
        if self.blocked:
            status = "Bloqué"
        return f"{self.username} - {status} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
