from django.urls import path

from accounts.permissions import django_superuser_required
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'  # optionnel mais pratique pour les namespaces

urlpatterns = [
    # Gestion administrateurs
    #path('admins/ajouter/', views.creer_admin, name='creer_admin'),  # 
    # URLs pour la gestion des admins
    path('admins/', views.liste_admins, name='liste_admins'),
    path('admins/creer/', views.creer_admin, name='creer_admin'),
    # path('admins/<int:admin_id>/', views.detail_admin, name='detail_admin'),  # Optionnel
    # path('admins/<int:admin_id>/modifier/', views.modifier_admin, name='modifier_admin'),  # Optionnel

    # Gestion étudiants
    path('etudiants/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/ajouter/', views.creer_etudiant, name='creer_etudiant'),
    path('etudiants/recherche/', views.rechercher_etudiants_ajax, name='recherche_etudiants_ajax'),
    path('etudiants/export/', views.export_etudiants_csv, name='export_etudiants_csv'),
    path('professeurs/export/', views.export_professeurs_csv, name='export_professeurs_csv'),


    # Gestion professeurs
    path('professeurs/', views.liste_professeurs, name='liste_professeurs'),
    path('professeurs/ajouter/', views.creer_professeur, name='creer_professeur'),
    path('professeurs/recherche/', views.rechercher_professeurs_ajax, name='recherche_professeurs_ajax'),

    path('etudiants/<int:etudiant_id>/modifier/', views.modifier_etudiant, name='modifier_etudiant'),
    path('etudiants/<int:etudiant_id>/supprimer/', views.supprimer_etudiant, name='supprimer_etudiant'),
    path('professeurs/<int:professeur_id>/modifier/', views.modifier_professeur, name='modifier_professeur'),
    path('professeurs/<int:professeur_id>/supprimer/', views.supprimer_professeur, name='supprimer_professeur'),

    path('users/gestion_utilisateurs/', views.gestion_utilisateurs, name='gestion_utilisateurs'),
    path('utilisateur/<int:user_id>/', views.detail_utilisateur, name='detail_utilisateur'),
    path('users/<int:user_id>/toggle_activation', views.toggle_activation, name='toggle_activation'),
    path('utilisateur/<int:user_id>/changer-role/', views.changer_role, name='changer_role'),
     
    # Authentification et dashboard
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-username/', views.check_username, name='check_username'),
    path('logout/confirm/', views.logout_confirm, name='logout_confirm'),  # ✅ AJOUT
    path('change-password-required/', views.change_password_required, name='change_password_required'),  # ✅ AJOUT
    path('password/change/', auth_views.PasswordChangeView.as_view(template_name='accounts/change_password.html', success_url='/comptes/password/change/done/'), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/change_password_done.html'), name='password_change_done'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mon-profil/', views.mon_profil, name='mon_profil'),
    # accounts/urls.py
    path('audit/', views.vue_audit, name='audit'), #audit
    path('login-attempts/', views.login_attempts_view, name='login_attempts'), #login attempt 
    path('update-activity/', views.update_activity, name='update_activity'),
    path('debug-session/', views.debug_session, name='debug_session'),

    path('utilisateurs/<int:user_id>/profil/', views.voir_profil_utilisateur, name='voir_profil_utilisateur'),
    # accounts/urls.py
    path('professeur/<int:user_id>/', views.voir_professeur_cours, name='voir_professeur'),

    #password reset urls
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/comptes/password-reset/done/'), name='password_reset'), 
    path('systeme/admins/', django_superuser_required(views.liste_admins_systeme), name='liste_admins_systeme'),         
    path('systeme/creer-admin/', django_superuser_required(views.creer_admin_systeme), name='creer_admin_systeme'),
    path('admins/modifier/<int:admin_id>/', views.modifier_admin, name='modifier_admin'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', success_url='/comptes/reset/done/'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_complete.html' ), name='password_reset_complete'),

    path('aide/', views.aide, name='aide'),

]
