# grades/urls.py
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # Professeur
    path('saisie-notes/<int:cours_id>/', views.saisie_notes, name='saisie_notes'),
    
    # Admin
    path('validation-notes/', views.validation_notes, name='validation_notes'),
    path('validation-notes/<int:cours_id>/traiter/', views.traiter_cours_notes, name='traiter_cours_notes'),
    path('notes-publiees/', views.gestion_notes_publiees, name='gestion_notes_publiees'),
    path('remettre-brouillon/<int:cours_id>/', views.remettre_notes_brouillon, name='remettre_notes_brouillon'),
    # Étudiant
    path('mes-notes/', views.consulter_notes_etudiant, name='consulter_notes_etudiant'),

    path('gestion-semestres/', views.gestion_semestres, name='gestion_semestres'),
    #SECTION RELEVEE DE NOTES
    # Nouveaux URLs pour les relevés
    path('releves/generer/', views.generer_releves_semestre, name='generer_releves'),
    path('releves/gestion/', views.gestion_releves, name='gestion_releves'),
    path('releves/<int:releve_id>/', views.consulter_releve_etudiant, name='detail_releve'),
    path('releves/mes-releves/', views.consulter_releve_etudiant, name='mes_releves'),
    path('cours/<int:cours_id>/releve/', views.releve_par_cours, name='releve_par_cours'),
    path('releves/<int:releve_id>/export-csv/', views.exporter_releve_csv, name='exporter_releve_csv'),
    path('historique/<int:etudiant_id>/', views.historique_complet_etudiant, name='historique_etudiant'),
    path('historique/mon-historique/', views.historique_complet_etudiant, name='mon_historique'),
    path('releves/gestion-complete/', views.gestion_releves_complete, name='gestion_releves_complete'),
     # URLs AJAX pour les relevés
    path('api/stats-releves/', views.api_stats_releves, name='api_stats_releves'),
    path('api/simulation-releves/', views.api_simulation_releves, name='api_simulation_releves'),
]