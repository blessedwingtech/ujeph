from django.contrib import admin
from .models import Note, MoyenneSemestre

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'cours', 'valeur', 'type_evaluation', 'statut', 'created_by', 'date_modification')
    list_filter = ('cours__faculte', 'cours__niveau', 'statut', 'type_evaluation', 'cours__semestre')
    search_fields = ('etudiant__user__first_name', 'etudiant__user__last_name', 'cours__intitule')
    list_editable = ('statut',)
    readonly_fields = ('date_creation', 'date_modification')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'etudiant__user', 'cours', 'created_by'
        )

@admin.register(MoyenneSemestre)
class MoyenneSemestreAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'semestre', 'annee_academique', 'moyenne', 'date_calcul')
    list_filter = ('semestre', 'annee_academique')
    search_fields = ('etudiant__user__first_name', 'etudiant__user__last_name')