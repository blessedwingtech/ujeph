from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # ✅ Admin seulement
    path('gestion-cours/', views.gestion_cours, name='gestion_cours'),
    
    # ✅ Professeurs
    path('mes-cours/', views.mes_cours_professeur, name='mes_cours_professeur'),
    
    # ✅ Étudiants
    path('mes-cours-etudiant/', views.mes_cours_etudiant, name='mes_cours_etudiant'),
    path('cours/recherche_/', views.rechercher_cours_ajax, name='recherche_cours_ajax'),
    path('cours/recherche/', views.recherche_cours_ajax, name='recherche_cours_ajax'),

    
    # ✅ Consultation générale (admin peut tout voir)
    path('facultes/', views.liste_facultes, name='liste_facultes'),
    path('cours/creer/', views.creer_cours, name='creer_cours'), 

    path('cours/', views.liste_cours, name='liste_cours'),
    path('facultes/', views.liste_facultes, name='liste_facultes'),

    path('cours/<int:cours_id>/modifier/', views.modifier_cours, name='modifier_cours'),
    path('cours/<int:cours_id>/supprimer/', views.supprimer_cours, name='supprimer_cours'),
    path('facultes/<int:faculte_id>/modifier/', views.modifier_faculte, name='modifier_faculte'),
    path('facultes/<int:faculte_id>/supprimer/', views.supprimer_faculte, name='supprimer_faculte'),

    #path('facultes/', views.liste_facultes, name='liste_facultes'),
    path('facultes/creer/', views.creer_faculte, name='creer_faculte'),  

    path('cours/export/',views.export_cours_csv, name='export_cours_csv'),

    path('cours/modal/', views.cours_par_faculte_modal, name='cours_modal'),
    path('annonce/modal/', views.annonce_detail_modal, name='annonce_modal'),
 

    # ✅ NOUVELLES URLs pour les annonces (AJOUTEZ CES LIGNES)
    # Liste et gestion des annonces
    path('annonces/', views.liste_annonces, name='liste_annonces'),
    path('annonces/creer/', views.creer_annonce, name='creer_annonce'),
    path('annonces/<int:pk>/editer/', views.editer_annonce, name='editer_annonce'),
    path('annonces/<int:pk>/supprimer/', views.supprimer_annonce, name='supprimer_annonce'),
    path('annonces/<int:pk>/toggle-publie/', views.toggle_publie, name='toggle_publie'),
    
    # Consultation publique des annonces (pour API ou vue séparée)
    path('annonces/actives/', views.annonces_actives, name='annonces_actives'),
    
    # URLs pour les filtres (optionnel)
    path('annonces/type/<str:type_annonce>/', views.annonces_par_type, name='annonces_par_type'),
    path('annonces/faculte/<int:faculte_id>/', views.annonces_par_faculte, name='annonces_par_faculte'),
    
    # Export/Import (optionnel)
    path('annonces/export/', views.export_annonces, name='export_annonces'),

    path('mes-annonces/', views.mes_annonces, name='mes_annonces'),
]





 