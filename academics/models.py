from django.db import models 
from accounts.models import User, Etudiant 
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Faculte(models.Model):
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_creation = models.DateField(auto_now_add=True)
    
    # Nouveau champ simple pour l'icône
    icone = models.CharField(
        max_length=30,
        default='fa-university',
        help_text="Nom de l'icône FontAwesome (ex: fa-laptop, fa-stethoscope, fa-leaf)"
    )
    
    def __str__(self):
        return self.nom
    
    def get_etudiants_count(self):
        """Retourne le nombre d'étudiants dans cette faculté"""
        from accounts.models import Etudiant
        return Etudiant.objects.filter(faculte=self).count()
    
    def get_cours_count(self):
        """Retourne le nombre de cours dans cette faculté"""
        return self.cours_set.count()


class Cours(models.Model):
    NIVEAU_CHOICES = [
        ('1ere', '1ère année'),
        ('2e', '2e année'), 
        ('3e', '3e année'),
        ('4e', '4e année'),
        ('5e', '5e année'),
    ]
    
    SEMESTRE_CHOICES = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    intitule = models.CharField(max_length=200)
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES)
    semestre = models.CharField(max_length=10, choices=SEMESTRE_CHOICES)
    credits = models.IntegerField(default=1, editable=False)
    faculte = models.ForeignKey(Faculte, on_delete=models.CASCADE)
    professeur = models.ForeignKey(
        User, 
        limit_choices_to={'role': 'prof'}, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Professeur assigné"
    )

    class Meta:
        verbose_name_plural = "Cours"
        unique_together = ['code', 'faculte', 'niveau', 'semestre']
    
    def __str__(self):
        return f"{self.code} - {self.intitule} ({self.get_niveau_display()} - {self.semestre})"
    
    def etudiants_concernes(self):
        """Retourne tous les étudiants concernés par ce cours"""
        return Etudiant.objects.filter(
            faculte=self.faculte,
            niveau=self.niveau
        )
    @property
    def nombre_etudiants(self):
        """Retourne le nombre d'étudiants inscrits à ce cours"""
        return self.inscriptions.count()  # via InscriptionCours




class Annonce(models.Model): 
    TYPE_CHOICES = [
        ('general', 'Générale'),
        ('academique', 'Académique'),
        ('urgence', 'Urgence'),
        ('evenement', 'Événement'),
        ('emploi', 'Offre d\'emploi'),
    ]
    
    # CORRECTION: 'urgence' apparaît deux fois, remplacez par 'critique'
    PRIORITE_CHOICES = [
        ('faible', 'Faible'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),  # ← Changé ici
    ]
    
    # ... reste du modèle inchangé ...
    
    titre = models.CharField(max_length=200, verbose_name="Titre de l'annonce")
    contenu = models.TextField(verbose_name="Contenu")
    type_annonce = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='general',
        verbose_name="Type d'annonce"
    )
    priorite = models.CharField(
        max_length=20, 
        choices=PRIORITE_CHOICES, 
        default='normale',
        verbose_name="Priorité"
    )
    
    # Destinataires
    destinataire_tous = models.BooleanField(default=True, verbose_name="Pour tous")
    destinataire_etudiants = models.BooleanField(default=False, verbose_name="Étudiants uniquement")
    destinataire_professeurs = models.BooleanField(default=False, verbose_name="Professeurs uniquement")
    destinataire_admins = models.BooleanField(default=False, verbose_name="Administrateurs uniquement")
    
    # Faculté spécifique (optionnel)
    faculte = models.ForeignKey(
        'academics.Faculte', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Faculté concernée (optionnel)"
    )
    
    # Dates
    date_publication = models.DateTimeField(default=timezone.now, verbose_name="Date de publication")
    date_expiration = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date d'expiration (optionnel)"
    )
    
    # Auteur
    auteur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='annonces_publiees',
        verbose_name="Auteur"
    )
    
    # Statut
    est_publie = models.BooleanField(default=True, verbose_name="Publié")
    est_important = models.BooleanField(default=False, verbose_name="Important")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    fichier_joint = models.FileField(
        upload_to='annonces/fichiers/%Y/%m/%d/',
        blank=True, 
        null=True,
        verbose_name="Fichier joint"
    )
    
    # Image (optionnel)
    image = models.ImageField(
        upload_to='annonces/images/%Y/%m/%d/',
        blank=True, 
        null=True,
        verbose_name="Image illustrative"
    )
    
    class Meta:
        ordering = ['-date_publication', '-priorite']
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        indexes = [
            models.Index(fields=['est_publie', 'date_publication']),
            models.Index(fields=['type_annonce']),
            models.Index(fields=['priorite']),
        ]
    
    def __str__(self):
        return self.titre
    
    @property
    def est_expiree(self):
        """Vérifie si l'annonce est expirée"""
        if self.date_expiration:
            return timezone.now() > self.date_expiration
        return False
    
    @property
    def est_active(self):
        """Vérifie si l'annonce est active (publiée et non expirée)"""
        return self.est_publie and not self.est_expiree
    
    @property
    def duree_restante(self):
        """Calcule le temps restant avant expiration"""
        if self.date_expiration:
            remaining = self.date_expiration - timezone.now()
            if remaining.days > 0:
                return f"{remaining.days} jour(s)"
            elif remaining.seconds > 3600:
                return f"{remaining.seconds // 3600} heure(s)"
            else:
                return "Moins d'une heure"
        return None
    
    def get_badge_color(self):
        """Retourne la couleur Bootstrap en fonction du type"""
        colors = {
            'general': 'primary',
            'academique': 'info',
            'urgence': 'danger',
            'evenement': 'success',
            'emploi': 'warning',
        }
        return colors.get(self.type_annonce, 'secondary')
    
    def get_icon(self):
        """Retourne l'icône Bootstrap en fonction du type"""
        icons = {
            'general': 'bi-megaphone',
            'academique': 'bi-book',
            'urgence': 'bi-exclamation-triangle',
            'evenement': 'bi-calendar-event',
            'emploi': 'bi-briefcase',
        }
        return icons.get(self.type_annonce, 'bi-bell')

 