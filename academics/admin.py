from django.contrib import admin
from .models import Faculte, Cours  # ✅ SEULEMENT Faculte et Cours

@admin.register(Faculte)
class FaculteAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'date_creation')
    search_fields = ('code', 'nom')
    list_filter = ('date_creation',)

@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ('code', 'intitule', 'faculte', 'niveau', 'semestre', 'professeur')
    list_filter = ('faculte', 'niveau', 'semestre')
    search_fields = ('code', 'intitule')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "professeur":
            from accounts.models import User
            kwargs["queryset"] = User.objects.filter(role='prof')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    


from django.contrib import admin
from .models import Annonce

@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_annonce', 'est_publie', 'date_publication', 'auteur']
    list_filter = ['est_publie', 'type_annonce', 'date_publication']
    search_fields = ['titre', 'contenu']