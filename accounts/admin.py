from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Etudiant, Professeur, Admin  # ✅ AJOUTER Admin
from academics.models import Faculte

# Dans admin.py - Améliorer l'admin User
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'date_creation', 'first_login')
    list_filter = ('role', 'is_staff', 'is_superuser', 'first_login')
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle dans le système', {'fields': ('role', 'telephone', 'first_login')}),
    )
    readonly_fields = ('date_creation',)
    actions = ['make_admin', 'make_professor', 'make_student']
    
    def make_admin(self, request, queryset):
        queryset.update(role=User.Role.ADMIN)
    make_admin.short_description = "Définir comme Administrateur"
    
    def make_professor(self, request, queryset):
        queryset.update(role=User.Role.PROFESSEUR)
    make_professor.short_description = "Définir comme Professeur"
    
    def make_student(self, request, queryset):
        queryset.update(role=User.Role.ETUDIANT)
    make_student.short_description = "Définir comme Étudiant"


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('get_nom', 'niveau_acces', 'date_nomination', 'get_permissions')
    list_filter = ('niveau_acces', 'date_nomination')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    
    # ✅ Filtrer les users qui sont administrateurs
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "user":
    #         kwargs["queryset"] = User.objects.filter(role=User.Role.ADMIN)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_nom(self, obj):
        return obj.user.get_full_name()
    get_nom.short_description = 'Nom Complet'
    
    def get_permissions(self, obj):
        permissions = []
        if obj.peut_gerer_utilisateurs:
            permissions.append("👥 Users")
        if obj.peut_gerer_cours:
            permissions.append("📚 Cours")
        if obj.peut_valider_notes:
            permissions.append("📝 Notes")
        if obj.peut_gerer_facultes:
            permissions.append("🏛️ Facultés")
        return " | ".join(permissions) if permissions else "Aucune"
    get_permissions.short_description = 'Permissions'

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'get_nom', 'faculte', 'niveau', 'date_inscription')
    list_filter = ('faculte', 'niveau', 'sexe')
    search_fields = ('matricule', 'user__first_name', 'user__last_name')
    
    # Filtrer les users qui sont étudiants
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "user":
    #         kwargs["queryset"] = User.objects.filter(role=User.Role.ETUDIANT)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_nom(self, obj):
        return obj.user.get_full_name()
    get_nom.short_description = 'Nom Complet'

@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('get_nom', 'specialite', 'statut', 'date_embauche')
    search_fields = ('user__first_name', 'user__last_name')
    
    # Filtrer les users qui sont professeurs
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "user":
    #         kwargs["queryset"] = User.objects.filter(role=User.Role.PROFESSEUR)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_nom(self, obj):
        return obj.user.get_full_name()
    get_nom.short_description = 'Nom'



# Dans accounts/admin.py, ajoutez :

from .models import AuditAction

@admin.register(AuditAction)
class AuditActionAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'action', 'objet', 'faculte']
    list_filter = ['action', 'user', 'date', 'faculte']
    search_fields = ['user', 'objet', 'details']
    readonly_fields = ['full_details']
    date_hierarchy = 'date'
    
    def full_details(self, obj):
        return f"""
        Date: {obj.date.strftime('%d/%m/%Y %H:%M:%S')}
        Utilisateur: {obj.user}
        Action: {obj.get_action_display()}
        Objet: {obj.objet}
        Faculté: {obj.faculte or 'N/A'}
        Cours: {obj.cours or 'N/A'}
        
        Détails:
        {obj.details}
        """
    