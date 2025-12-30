from django.db import models
from accounts.models import Etudiant, Professeur, User
from academics.models import Cours, Faculte
from datetime import timezone
from django.utils import timezone

class Note(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumise', 'Soumise pour validation'),
        ('publiée', 'Publiée (visible étudiant)'),
        ('rejetée', 'Rejetée'),
    ]
    
    TYPE_EVALUATION = [
        ('examen', 'Examen'),
        ('tp', 'Travail Pratique'),
        ('projet', 'Projet'),
        ('partiel', 'Partiel'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Étudiant")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, verbose_name="Cours")
    valeur = models.FloatField(verbose_name="Note", help_text="Note sur 100")
    type_evaluation = models.CharField(max_length=20, choices=TYPE_EVALUATION, default='examen')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    
    # ✅ NOUVEAU : Motif de rejet
    motif_rejet = models.TextField(blank=True, null=True, verbose_name="Motif du rejet")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_soumission = models.DateTimeField(blank=True, null=True)  # ✅ NOUVEAU
    date_validation = models.DateTimeField(blank=True, null=True)  # ✅ NOUVEAU
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.Role.PROFESSEUR},
        null=True,
        blank=True,
        verbose_name="Professeur"
    )
    annee_academique = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name="Année académique",
        help_text="Format: 2023-2024"
    )
    
    class Meta:
        verbose_name_plural = "Notes"
        unique_together = ['etudiant', 'cours', 'type_evaluation']
        ordering = ['cours', 'etudiant']
    
    def __str__(self):
        return f"{self.etudiant} - {self.cours}: {self.valeur}/100"
    
    def est_valide(self):
        """Valide que la note est entre 0 et 100"""
        return 0 <= self.valeur <= 100
    
    def get_statut_display_color(self):
        """Retourne la couleur Bootstrap selon le statut"""
        colors = {
            'brouillon': 'secondary',
            'soumise': 'warning', 
            'publiée': 'success',
            'rejetée': 'danger'
        }
        return colors.get(self.statut, 'secondary')
    # models.py - Ajoutez cette méthode dans la classe Note
    def remettre_en_brouillon(self):
        """Remet une note publiée en brouillon (action admin)"""
        if self.statut == 'publiée':
            self.statut = 'brouillon'
            self.date_validation = None  # Réinitialiser la date de validation
            self.save()
            return True
        return False
    
    
    # ✅ NOUVEAU : Méthodes de workflow
    def peut_modifier_par(self, user):
        """Vérifie si l'utilisateur peut modifier cette note"""
        if user.role == User.Role.PROFESSEUR:
            return (self.created_by == user and 
                   self.statut in ['brouillon', 'rejetée'])
        return False
    
    def soumettre(self):
        """Soumet la note pour validation"""
        if self.statut == 'brouillon':
            self.statut = 'soumise'
            self.date_soumission = timezone.now()
            self.save()
    
    def publier(self):
        """Publie la note (validation admin)"""
        if self.statut == 'soumise':
            self.statut = 'publiée'
            self.date_validation = timezone.now()
            self.motif_rejet = None  # Reset le motif si précédemment rejetée
            self.save()
    
    def rejeter(self, motif):
        """Rejette la note avec motif"""
        if self.statut == 'soumise':
            self.statut = 'rejetée'
            self.motif_rejet = motif
            self.save()
    
    @property
    def est_modifiable(self):
        """Vérifie si la note est modifiable (pour usage template)"""
        return self.statut in ['brouillon', 'rejetée']
    
    def peut_modifier_par(self, user):
        """Vérifie si l'utilisateur peut modifier cette note"""
        if user.role == User.Role.PROFESSEUR:
            return (self.created_by == user and 
                   self.statut in ['brouillon', 'rejetée'])
        return False
    

class MoyenneSemestre(models.Model):
    """Moyenne par semestre pour un étudiant"""
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    semestre = models.CharField(max_length=10, choices=[('S1', 'Semestre 1'), ('S2', 'Semestre 2')])
    annee_academique = models.CharField(max_length=9, default='2025-2026')
    moyenne = models.FloatField()
    date_calcul = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['etudiant', 'semestre', 'annee_academique']
    
    def __str__(self):
        return f"{self.etudiant} - {self.semestre} {self.annee_academique}: {self.moyenne:.2f}"
    


class InscriptionCours(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='inscriptions')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='inscriptions')
    date_inscription = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['etudiant', 'cours']
        verbose_name = "Inscription à un cours"
        verbose_name_plural = "Inscriptions aux cours"

    def __str__(self):
        return f"{self.etudiant} → {self.cours}"


# Dans grades/models.py - AJOUTER à la fin du fichier

class HistoriquePromotion(models.Model):
    """Trace les changements de niveau/semestre"""
    
    DECISION_CHOICES = [
        ('admis', 'Admis'),
        ('redouble', 'Redouble'),
        ('passage_conditionnel', 'Passage conditionnel'),
        ('changement_semestre', 'Changement de semestre'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='promotions')
    ancien_niveau = models.CharField(max_length=50)
    ancien_semestre = models.CharField(max_length=10)
    nouveau_niveau = models.CharField(max_length=50)
    nouveau_semestre = models.CharField(max_length=10)
    annee_academique = models.CharField(max_length=9)
    decision = models.CharField(max_length=50, choices=DECISION_CHOICES)
    moyenne_generale = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    date_promotion = models.DateTimeField(auto_now_add=True)
    effectue_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_promotion']
        verbose_name = "Historique de promotion"
        verbose_name_plural = "Historiques de promotions"
    
    def __str__(self):
        return f"{self.etudiant.matricule} - {self.ancien_niveau}{self.ancien_semestre} → {self.nouveau_niveau}{self.nouveau_semestre}"
    

# grades/models.py - AJOUTEZ APRÈS les autres modèles

class ReleveDeNotes(models.Model):
    """Archive structurée des relevés de notes par semestre/année"""
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='releves')
    annee_academique = models.CharField(max_length=9)
    semestre = models.CharField(max_length=10, choices=[('S1', 'Semestre 1'), ('S2', 'Semestre 2')])
    
    # Moyennes calculées
    moyenne_semestre = models.DecimalField(max_digits=5, decimal_places=2)
    moyenne_cumulee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    moyenne_generale = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Détails des notes (stocké en JSON pour l'archivage)
    details_notes = models.JSONField(default=dict, help_text="Structure JSON des notes")
    
    # Informations académiques au moment du relevé
    niveau = models.CharField(max_length=10)
    faculte = models.ForeignKey(Faculte, on_delete=models.SET_NULL, null=True)
    statut = models.CharField(max_length=20, default='actif')
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(auto_now=True)
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='releves_valides')
    
    # PDF généré (optionnel)
    fichier_pdf = models.FileField(upload_to='releves/%Y/%m/%d/', null=True, blank=True)
    
    class Meta:
        unique_together = ['etudiant', 'annee_academique', 'semestre']
        ordering = ['-annee_academique', 'semestre']
        verbose_name = "Relevé de notes"
        verbose_name_plural = "Relevés de notes"
    
    def __str__(self):
        return f"Relevé {self.etudiant.matricule} - {self.annee_academique} {self.semestre}"
    
    def calculer_stats(self):
        """Calcule les statistiques à partir des détails"""
        if not self.details_notes.get('notes'):
            return None
        
        notes = self.details_notes['notes']
        total_points = sum(n['note'] for n in notes)
        total_coefficients = sum(n.get('coefficient', 1) for n in notes)
        
        return {
            'nb_cours': len(notes),
            'moyenne_ponderee': round(total_points / total_coefficients, 2),
            'note_max': max(n['note'] for n in notes),
            'note_min': min(n['note'] for n in notes),
            'cours_valides': sum(1 for n in notes if n['note'] >= 70),  # Seuil UJEPH
            'cours_echoues': sum(1 for n in notes if n['note'] < 70),
        }
