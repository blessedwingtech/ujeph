# academics/forms.py
from django import forms
from .models import Cours, Faculte
from accounts.models import User
# forms.py 
from django.utils import timezone
from .models import Annonce 


# academics/forms.py
class FaculteForm(forms.ModelForm):
    class Meta:
        model = Faculte
        fields = ['code', 'nom', 'description', 'icone']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'INFO-x (max 10 caractères)',
                'maxlength': 10
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Sciences Informatiques'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la faculté...'
            }),
            'icone': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'code': 'Code de la faculté',
            'nom': 'Nom de la faculté', 
            'description': 'Description'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir les choix d'icônes
        self.fields['icone'].widget.choices = [
            ('fa-university', '🏛️ Général (fa-university)'),
            ('fa-laptop', '💻 Informatique (fa-laptop)'),
            ('fa-stethoscope', '🏥 Médecine/Santé (fa-stethoscope)'),
            ('fa-leaf', '🌱 Agronomie/Environnement (fa-leaf)'),
            ('fa-book', '📚 Théologie/Lettres (fa-book)'),
            ('fa-chart-line', '📈 Administration/Gestion (fa-chart-line)'),
            ('fa-balance-scale', '⚖️ Droit (fa-balance-scale)'),
            ('fa-flask', '🧪 Sciences (fa-flask)'),
            ('fa-palette', '🎨 Arts (fa-palette)'),
            ('fa-chalkboard-teacher', '👨‍🏫 Éducation (fa-chalkboard-teacher)'),
            ('fa-graduation-cap', '🎓 Formation générale (fa-graduation-cap)'),
        ]
        


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ['code', 'intitule', 'niveau', 'semestre', 'faculte', 'professeur']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control','placeholder': 'STAT-x', 'required': True}),
            'intitule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du cours', 'required': True}),
            'niveau': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'semestre': forms.Select(attrs={'class': 'form-select', 'required': True}), 
            'faculte': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'professeur': forms.Select(attrs={'class': 'form-select', 'required': True}), 
        }
        labels = {
            'intitule': 'Intitulé du cours',
            'professeur': 'Professeur assigné'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professeur'].queryset = User.objects.filter(
            role=User.Role.PROFESSEUR
        ).order_by('first_name', 'last_name')
        self.fields['professeur'].empty_label = "Sélectionnez un professeur"




class AnnonceForm(forms.ModelForm):
    class Meta:
        model = Annonce
        # Retirez 'date_publication' car elle est gérée automatiquement
        # Retirez 'auteur' car il est défini dans la vue
        fields = [
            'titre', 'contenu', 'type_annonce', 'priorite',
            'destinataire_tous', 'destinataire_etudiants', 
            'destinataire_professeurs', 'destinataire_admins',
            'faculte', 'date_expiration',
            'est_publie', 'est_important', 'fichier_joint', 'image'  # ← Changé ici
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de l\'annonce'
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Contenu détaillé de l\'annonce...'
            }),
            'type_annonce': forms.Select(attrs={'class': 'form-select'}),
            'priorite': forms.Select(attrs={'class': 'form-select'}),
            'date_expiration': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'faculte': forms.Select(attrs={'class': 'form-select'}),
            # Ajoutez les widgets pour les booléens si besoin
            'est_publie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'est_important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destinataire_tous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destinataire_etudiants': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destinataire_professeurs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destinataire_admins': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'titre': 'Titre',
            'contenu': 'Contenu',
            'type_annonce': 'Catégorie',
            'priorite': 'Niveau de priorité',
            'date_expiration': 'Date et heure d\'expiration (optionnel)',
            'fichier_joint': 'Fichier joint',  # ← Changé ici
            'image': 'Image illustrative',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Facultés optionnelles
        self.fields['faculte'].queryset = Faculte.objects.all()
        self.fields['faculte'].required = False
        self.fields['date_expiration'].required = False
        self.fields['fichier_joint'].required = False
        self.fields['image'].required = False
        
        # Ajoutez des classes CSS aux champs
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ['TextInput', 'DateTimeInput', 'Select']:
                field.widget.attrs.setdefault('class', 'form-control')

