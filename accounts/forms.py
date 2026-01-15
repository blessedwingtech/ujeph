from django import forms
from .models import Admin, User, Etudiant, Professeur
from academics.models import Faculte 
from django.contrib.auth.forms import UserChangeForm 
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator



class UserForm(forms.ModelForm):
    # Ne pas rendre le champ password obligatoire dans le formulaire
    password = forms.CharField(
        required=False,  # Important !
        widget=forms.PasswordInput(attrs={'class': 'form-control d-none'}),  # Caché
        help_text="Laissez vide pour utiliser le mot de passe par défaut '1234'"
    )

    # Ajouter cette ligne pour rendre le téléphone optionnel
    telephone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}), 
        }
    

# forms.py
class EtudiantForm(forms.ModelForm):
    faculte = forms.ModelChoiceField(
        queryset=Faculte.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Faculté"
    )
    telephone_parent = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{7,14}$',
                message="Numéro invalide. Utilisez le format international (ex: +33123456789)."
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Etudiant
        exclude = ['user', 'date_inscription', 'matricule', 'annee_academique_courante', 'statut_academique']  # Exclure matricule
        widgets = {
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'semestre_courant': forms.Select(attrs={'class': 'form-select'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'telephone_parent': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        
        # Déterminer le semestre par défaut basé sur le mois
        mois = timezone.now().month
        semestre_default = 'S1' if (9 <= mois <= 12 or mois == 1) else 'S2'
        
        # Définir la valeur initiale
        self.fields['semestre_courant'].initial = semestre_default
        
        # Aide à la décision
        self.fields['semestre_courant'].help_text = f"Semestre suggéré: {semestre_default} (mois actuel: {mois})"

        
class ProfesseurForm(forms.ModelForm):
    class Meta:
        model = Professeur
        exclude = ['user']
        widgets = {
            'specialite': forms.TextInput(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }



class UserEditForm(forms.ModelForm):
    """Formulaire pour modifier un utilisateur existant (sans password)"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}), 
        }
 



class UserProfileForm(UserChangeForm):
    """Formulaire pour modifier les informations personnelles de l'utilisateur"""
    
    # Masquer le champ password
    password = None
    
    # Champs personnalisés selon le type d'utilisateur
    adresse = forms.CharField(
        max_length=200,
        required=False,
        label="Adresse",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Votre adresse complète'
        })
    )
    
    telephone_parent = forms.CharField(
        max_length=20,
        required=False,
        label="Téléphone du parent/tuteur",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243...'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'telephone']  # Seuls champs modifiables
        labels = {
            'email': 'Adresse email',
            'telephone': 'Téléphone',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'votre@email.com'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre l'email obligatoire
        self.fields['email'].required = True
        
        # Ajouter les champs spécifiques selon le rôle
        user = self.instance
        
        # Pour les étudiants
        if user.role == 'student':
            try:
                etudiant = Etudiant.objects.get(user=user)
                self.fields['adresse'].initial = etudiant.adresse
                self.fields['telephone_parent'].initial = etudiant.telephone_parent
            except ObjectDoesNotExist:
                pass
        
        # Pour les professeurs (si besoin d'ajouter des champs spécifiques)
        elif user.role == 'prof':
            # Vous pouvez ajouter des champs spécifiques aux professeurs ici
            pass
        
        # Organiser l'ordre des champs
        self.fields['email'].label = "📧 Adresse email"
        self.fields['telephone'].label = "📱 Téléphone personnel"
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        
        # Sauvegarder les champs spécifiques aux étudiants
        if user.role == 'student':
            try:
                etudiant = Etudiant.objects.get(user=user)
                etudiant.adresse = self.cleaned_data.get('adresse', '')
                etudiant.telephone_parent = self.cleaned_data.get('telephone_parent', '')
                if commit:
                    etudiant.save()
            except ObjectDoesNotExist:
                pass
        
        # Pour les professeurs (si besoin)
        elif user.role == 'prof':
            pass
        
        return user
    

# forms.py - AJOUTE cette classe
class AdminCreationForm(forms.ModelForm):  # Hérite de UserForm
    niveau_acces = forms.ChoiceField(
        choices=[
            ('super', 'Super Administrateur (toutes permissions)'),
            ('academique', 'Administrateur Académique (pas de gestion utilisateurs)'),
            ('utilisateurs', 'Gestionnaire Utilisateurs (utilisateurs seulement)')
        ],
        initial='academique',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Niveau d'accès"
    )
    
    class Meta(UserForm.Meta):
        # Hérite tous les champs de UserForm
        pass
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre tous les champs requis
        for field_name, field in self.fields.items():
            if field_name != 'telephone':  # téléphone peut être optionnel
                field.required = True

            # AJOUTER CETTE LIGNE pour styliser le champ téléphone
        if 'telephone' in self.fields:
            self.fields['telephone'].widget.attrs.update({'class': 'form-control'})
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        # Rendre le mot de passe optionnel et caché
        # self.fields['password'].widget.attrs.update({'class': 'form-control'})
        # self.fields['password'].required = False
        # self.fields['password'].help_text = "Laissez vide pour '1234' par défaut"


# forms.py - VERSION OPTIMISÉE

# Pour la MODIFICATION, utiliser UserEditForm (pas UserForm)
# UserEditForm existe déjà dans votre code et est parfait

# Corriger AdminModificationForm
class AdminModificationForm(forms.ModelForm):
    """Formulaire pour modifier UNIQUEMENT les permissions admin"""
    niveau_acces = forms.ChoiceField(
        choices=[
            ('super', 'Super Administrateur (toutes permissions)'),
            ('academique', 'Administrateur Académique (pas de gestion utilisateurs)'),
            ('utilisateurs', 'Gestionnaire Utilisateurs (utilisateurs seulement)')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Niveau d'accès"
    )
    
    # PAS de champ password ici ! On le gère séparément
    
    class Meta:
        model = Admin
        fields = ['niveau_acces', 'peut_gerer_utilisateurs', 'peut_gerer_cours', 
                  'peut_valider_notes', 'peut_gerer_facultes']
        widgets = {
            'peut_gerer_utilisateurs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'peut_gerer_cours': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'peut_valider_notes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'peut_gerer_facultes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplifier - pas besoin de manipuler les attrs
        pass
