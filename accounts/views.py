from django.utils import timezone
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

from accounts.permissions import django_superuser_required
from .forms import AdminCreationForm, UserEditForm, UserForm, EtudiantForm, ProfesseurForm
from .models import LoginAttempt, User, Etudiant, Professeur, Admin, get_annee_academique  # ✅ Admin importé
from django.core.paginator import Paginator   
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST 
import json
import re
import secrets
import string 
from django.db import IntegrityError, transaction
from django.db.models import signals 
from .signals import create_user_profile 
 
from django.contrib import messages
from .forms import UserProfileForm 
from django.core.exceptions import ObjectDoesNotExist
 
from academics.models import Faculte 
from academics.models import Cours, Annonce 
 
from django.http import HttpResponse
from django.db.models import Q
import csv
import io 
 
import json, re
from .models import User  
from .models import User, Admin
from django.db import IntegrityError 

User = get_user_model() 
from django.db.models.signals import post_save
  
from django.db.models import Q
from .models import User, Etudiant, Professeur
 
from .audit_utils import (
    audit_action_generique, audit_creer_etudiant, audit_modifier_etudiant, audit_supprimer_etudiant,
    audit_creer_professeur, audit_modifier_professeur, audit_supprimer_professeur,
    audit_creer_admin, audit_login, audit_logout, audit_login_failed
)


 
 
def is_admin(user):
    return (
        user.is_authenticated and
        user.role == User.Role.ADMIN and
        hasattr(user, 'admin')
    )
# === FONCTIONS DE VÉRIFICATION DE PERMISSIONS ===

# === FONCTIONS DE VÉRIFICATION DE PERMISSIONS ===

# ⚠️ CRITIQUE - CETTE FONCTION DOIT EXISTER
def is_admin(user):
    """Vérifie si l'utilisateur est un admin du système"""
    return (
        user.is_authenticated and
        user.role == User.Role.ADMIN and
        hasattr(user, 'admin')
    )

# 1. SUPER ADMIN - Peut TOUT faire
def is_super_admin(user):
    """Vérifie si l'utilisateur est un Super Admin"""
    return is_admin(user) and user.admin.niveau_acces == 'super'

# 2. PERMISSIONS GRANULAIRES
def can_manage_users(user):
    """
    Vérifie si l'admin peut gérer les utilisateurs (étudiants, professeurs)
    """
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    return user.admin.peut_gerer_utilisateurs

# ✅ MODIFIÉ : MAINTENANT INCLUT COURS + FACULTÉS + NOTES
# accounts/views.py - MODIFIEZ CES FONCTIONS

# 1. can_manage_academique reste TRÈS RESTRICTIVE (les 3 permissions)
def can_manage_academique(user):
    """
    Vérifie si l'admin peut gérer TOUT ce qui est académique
    (cours + facultés + validation notes)
    Très restrictive - nécessite les 3 permissions
    """
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    return (
        user.admin.peut_gerer_cours and 
        user.admin.peut_gerer_facultes and 
        user.admin.peut_valider_notes
    )

# 2. can_manage_cours devient PLUS PERMISSIVE
def can_manage_cours(user):
    """
    Vérifie si l'admin peut gérer les cours
    Soit il a la permission spécifique, soit il a can_manage_academique
    """
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    return user.admin.peut_gerer_cours or can_manage_academique(user)  # ✅ MODIFIÉ

# 3. Faites de même pour les autres permissions académiques
def can_manage_facultes(user):
    """Vérifie si l'admin peut gérer les facultés"""
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    return user.admin.peut_gerer_facultes or can_manage_academique(user)  # ✅ MODIFIÉ

def can_validate_grades(user):
    """Vérifie si l'admin peut valider des notes"""
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    return user.admin.peut_valider_notes or can_manage_academique(user)  # ✅ MODIFIÉ

# 4. can_access_academique reste logique OU
def can_access_academique(user):
    """
    Vérifie si l'admin peut accéder à l'interface académique
    (au moins une permission académique spécifique OU can_manage_academique)
    """
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    
    # Soit une permission spécifique, soit la permission globale
    return (
        user.admin.peut_gerer_cours or 
        user.admin.peut_gerer_facultes or 
        user.admin.peut_valider_notes or
        can_manage_academique(user)  # ✅ AJOUTÉ
    )

def permission_required(test_func, message=None, redirect_url='accounts:dashboard'):
    """
    Messages simplifiés - un par type de permission
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            
            # Messages TRÈS SIMPLES comme vous voulez
            if message is None:
                func_name = test_func.__name__
                
                if func_name == 'can_manage_academique':
                    error_msg = "🎓 Vous n'avez pas accès à la gestion académique"
                elif func_name == 'can_manage_cours':
                    error_msg = "🎓 Vous n'avez pas accès à la gestion académique"
                elif func_name == 'can_manage_facultes':
                    error_msg = "🎓 Vous n'avez pas accès à la gestion académique"
                elif func_name == 'can_validate_grades':
                    error_msg = "🎓 Vous n'avez pas accès à la gestion académique"
                elif func_name == 'can_access_academique':
                    error_msg = "🎓 Vous n'avez pas accès à la gestion académique"
                    
                elif func_name == 'can_manage_users':
                    error_msg = "👥 Vous n'avez pas accès à la gestion des utilisateurs"
                elif func_name == 'can_manage_annonces':
                    error_msg = "👥 Vous n'avez pas accès à la gestion des utilisateurs"
                    
                elif func_name == 'is_admin':
                    error_msg = "👔 Accès réservé aux administrateurs"
                elif func_name == 'is_super_admin':
                    error_msg = "👑 Accès réservé aux super administrateurs"
                    
                else:
                    error_msg = "🔒 Accès non autorisé"
            else:
                error_msg = message
            
            messages.error(request, error_msg)
            return redirect(redirect_url)
        
        return wrapper
    return decorator


# ✅ AJOUTÉ : Gestion des annonces
def can_manage_annonces(user):
    """
    Vérifie si l'admin peut gérer les annonces
    Par défaut : tous les admins académiques peuvent gérer les annonces
    """
    if not is_admin(user):
        return False
    if is_super_admin(user):
        return True
    # Option 1: Tous les admins académiques peuvent gérer les annonces
    return can_manage_academique(user) or user.admin.peut_gerer_utilisateurs
    # Option 2: Tous les admins
    # return True

# 3. PERMISSION SPÉCIALE : CRÉER DES ADMINS
def can_manage_admins(user):
    """
    Vérifie si l'admin peut créer d'autres administrateurs
    SEULEMENT les Super Admins peuvent créer des admins
    """
    if not is_admin(user):
        return False
    return user.admin.niveau_acces == 'super'


# Ajoutez cette fonction dans academics/views.py
def get_annonces_accueil(request):
    """Récupère les annonces à afficher sur la page d'accueil"""
    from django.utils import timezone
    from academics.models import Annonce
    
    now = timezone.now()
    
    # Annonces actives (publiées et non expirées)
    annonces = Annonce.objects.filter(
        est_publie=True,
        date_publication__lte=now
    ).exclude(
        date_expiration__lt=now
    ).order_by('-est_important', '-priorite', '-date_publication')
    
    # Filtrer par destinataire si l'utilisateur est connecté
    if request.user.is_authenticated:
        if request.user.role == 'student':
            annonces = annonces.filter(
                destinataire_tous=True
            ) | annonces.filter(
                destinataire_etudiants=True
            )
        elif request.user.role == 'prof':
            annonces = annonces.filter(
                destinataire_tous=True
            ) | annonces.filter(
                destinataire_professeurs=True
            )
        elif request.user.role == 'admin':
            annonces = annonces.filter(
                destinataire_tous=True
            ) | annonces.filter(
                destinataire_admins=True
            )
    else:
        # Pour les visiteurs non connectés, uniquement les annonces "pour tous"
        annonces = annonces.filter(destinataire_tous=True)
    
    return annonces.distinct()[:10]  # Limiter à 10 annonces

def home(request):
    """Page d'accueil"""
    from academics.views import get_annonces_accueil
    from academics.models import Faculte
    from accounts.models import User
    
    # Récupérer les annonces actives
    annonces = get_annonces_accueil(request)
    
    # Récupérer toutes les facultés
    facultes = Faculte.objects.all()[:6]  # Limiter à 6 pour l'affichage
    
    # Statistiques (vous pouvez les remplacer par vos vraies données)
    context = {
        'annonces': annonces,
        'facultes': facultes,
        'total_etudiants': User.objects.filter(role='student').count(),
        'total_professeurs': User.objects.filter(role='prof').count(),
        'total_facultes': Faculte.objects.count(),
        'total_cours': Cours.objects.count() if 'Cours' in globals() else 85,
    }
    return render(request, 'home.html', context)





@require_POST
def check_username(request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()

        if not username:
            return JsonResponse({
                'exists': False,
                'valid': False,
                'message': 'Nom d\'utilisateur vide'
            })

        # Format correct : lettre ou underscore au début
        if not re.match(r'^[a-zA-Z_].*$', username):
            return JsonResponse({
                'exists': False,
                'valid': False,
                'message': 'Le nom doit commencer par une lettre ou underscore'
            })

        # Longueur minimale
        if len(username) < 3:
            return JsonResponse({
                'exists': False,
                'valid': False,
                'message': 'Minimum 3 caractères'
            })

        # Vérifier existence
        exists = User.objects.filter(username=username).exists()

        return JsonResponse({
            'exists': exists,
            'valid': True,
            'message': 'Nom déjà pris' if exists else 'Nom disponible'
        })

    except Exception as e:
        return JsonResponse({
            'exists': False,
            'valid': False,
            'message': f'Erreur serveur : {str(e)}'
        }, status=500)

# @require_POST
# def check_username(request):
#     """Vérifie si un nom d'utilisateur existe et valide le format"""
#     try:
#         data = json.loads(request.body)
#         username = data.get('username', '').strip()
        
#         if not username:
#             return JsonResponse({
#                 'exists': False,
#                 'valid': False,
#                 'message': 'Nom d\'utilisateur vide'
#             })
        
#         # Validation du format (lettre ou underscore au début)
#         is_valid_format = bool(re.match(r'^[a-zA-Z_].*$', username))
        
#         if not is_valid_format:
#             return JsonResponse({
#                 'exists': False,
#                 'valid': False,
#                 'message': 'Le nom d\'utilisateur doit commencer par une lettre ou underscore'
#             })
        
#         # Vérifier la longueur minimale
#         if len(username) < 3:
#             return JsonResponse({
#                 'exists': False,
#                 'valid': False,
#                 'message': 'Le nom d\'utilisateur doit contenir au moins 3 caractères'
#             })
        
#         # Vérifier si l'utilisateur existe
#         exists = User.objects.filter(username=username).exists()
        
#         return JsonResponse({
#             'exists': exists,
#             'valid': True,
#             'username': username,
#             'message': 'Utilisateur trouvé' if exists else 'Utilisateur non reconnu'
#         })
        
#     except json.JSONDecodeError:
#         return JsonResponse({
#             'error': 'Invalid JSON format',
#             'valid': False,
#             'exists': False
#         }, status=400)
#     except Exception as e:
#         return JsonResponse({
#             'error': str(e),
#             'valid': False,
#             'exists': False
#         }, status=500)
    

# accounts/views.py
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate, login 
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from .models import LoginAttempt
from .audit_utils import audit_login, audit_login_failed

def login_view(request):
    """Vue de connexion avec validation en temps réel et protection contre les attaques"""
    
    # Configuration de sécurité
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes en secondes
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Validation basique
        if not username or not password:
            return render(request, 'login.html', {
                'error': 'Veuillez remplir tous les champs',
                'remaining_attempts': MAX_ATTEMPTS,
                'form': {
                    'username': {'value': username or ''},
                    'password': {'value': ''}
                }
            })
        
        # Vérifier si l'utilisateur/IP est bloqué(e)
        from .middleware import get_client_ip
        ip_address = get_client_ip(request)
        
        # Clés pour le cache
        user_key = f"login_attempts_user_{username}"
        
        # Vérifier les tentatives et le timestamp
        cache_data = cache.get(user_key, {'attempts': 0, 'lock_time': None})
        user_attempts = cache_data['attempts']
        lock_time = cache_data.get('lock_time')
        
        # Si verrouillé, calculer le temps restant
        if lock_time:
            current_time = timezone.now()
            elapsed_time = (current_time - lock_time).total_seconds()
            remaining_lock_time = LOCKOUT_DURATION - elapsed_time
            
            if remaining_lock_time > 0:
                # Enregistrer la tentative bloquée
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=ip_address,
                    successful=False,
                    blocked=True
                )
                
                audit_login_failed(request, username)
                
                # Convertir en minutes et secondes pour l'affichage
                minutes = int(remaining_lock_time // 60)
                seconds = int(remaining_lock_time % 60)
                
                error_msg = f'⛔ Trop de tentatives de connexion. '
                
                if minutes > 0:
                    error_msg += f'Veuillez réessayer dans {minutes} minute(s)'
                    if seconds > 0:
                        error_msg += f' et {seconds} seconde(s)'
                else:
                    error_msg += f'Veuillez réessayer dans {seconds} seconde(s)'
                
                error_msg += '.'
                
                return render(request, 'login.html', {
                    'error': error_msg,
                    'remaining_attempts': 0,
                    'lockout_remaining': remaining_lock_time,
                    'form': {
                        'username': {'value': username},
                        'password': {'value': ''}
                    },
                    'lockout_active': True
                })
            else:
                # Le verrouillage est expiré, réinitialiser
                cache_data = {'attempts': 0, 'lock_time': None}
                cache.set(user_key, cache_data, LOCKOUT_DURATION)
        
        # Calculer les tentatives restantes AVANT la nouvelle tentative
        remaining_before = MAX_ATTEMPTS - user_attempts
        
        if user_attempts >= MAX_ATTEMPTS and not lock_time:
            # Premier dépassement, définir le timestamp de verrouillage
            cache_data = {
                'attempts': user_attempts,
                'lock_time': timezone.now()
            }
            cache.set(user_key, cache_data, LOCKOUT_DURATION)
            
            # Enregistrer la tentative bloquée
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                successful=False,
                blocked=True
            )
            
            audit_login_failed(request, username)
            
            return render(request, 'login.html', {
                'error': f'⛔ Trop de tentatives de connexion. Veuillez réessayer dans {LOCKOUT_DURATION//60} minutes.',
                'remaining_attempts': 0,
                'lockout_remaining': LOCKOUT_DURATION,
                'form': {
                    'username': {'value': username},
                    'password': {'value': ''}
                },
                'lockout_active': True
            })
        
        # CHERCHEZ L'UTILISATEUR (sans élever d'exception)
        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # AUDIT: Tentative avec nom d'utilisateur inexistant
            audit_login_failed(request, username)
            # Cherchez aussi par email si votre système le permet
            try:
                user = User.objects.get(email=username)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        
        if user is None:
            # Utilisateur n'existe pas
            audit_login_failed(request, username)
            
            # Enregistrer la tentative et incrémenter les compteurs
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                successful=False
            )
            
            user_attempts += 1
            remaining_after = MAX_ATTEMPTS - user_attempts
            
            if remaining_after <= 0:
                # Verrouiller maintenant
                cache_data = {
                    'attempts': user_attempts,
                    'lock_time': timezone.now()
                }
                error_msg = f'Nom d\'utilisateur non reconnu. Compte bloqué pendant {LOCKOUT_DURATION//60} minutes.'
            else:
                cache_data = {'attempts': user_attempts, 'lock_time': None}
                error_msg = f'Nom d\'utilisateur non reconnu. Il vous reste {remaining_after} tentative(s).'
            
            cache.set(user_key, cache_data, LOCKOUT_DURATION)
            
            return render(request, 'login.html', {
                'error': error_msg,
                'remaining_attempts': remaining_after,
                'form': {
                    'username': {'value': username},
                    'password': {'value': ''}
                }
            })
        
        # VÉRIFIEZ L'ÉTAT DU COMPTE
        if not user.is_active:
            # Compte désactivé - message précis
            audit_login_failed(request, username)
            
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                successful=False
            )
            
            user_attempts += 1
            remaining_after = MAX_ATTEMPTS - (user_attempts)
            cache_data['attempts'] = user_attempts
            cache.set(user_key, cache_data, LOCKOUT_DURATION)
            
            return render(request, 'login.html', {
                'error': '❌ <strong>Compte désactivé</strong><br>Votre compte a été désactivé par l\'administration. Veuillez contacter le support technique.',
                'remaining_attempts': remaining_after,
                'form': {
                    'username': {'value': username},
                    'password': {'value': ''}
                },
                'account_disabled': True
            })
        
        # TENTATIVE D'AUTHENTIFICATION
        auth_user = authenticate(request, username=user.username, password=password)
        
        if auth_user:
            # Connexion réussie - réinitialiser les compteurs
            cache.delete(user_key)
            
            # Enregistrer la tentative réussie
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                successful=True
            )
            
            login(request, auth_user)
            audit_login(request, auth_user)
            
            # Définir le timestamp de dernière activité
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Vérifier si premier login
            if hasattr(auth_user, 'first_login') and auth_user.first_login:
                messages.info(request, "Veuillez changer votre mot de passe pour la première connexion.")
                return redirect('accounts:change_password_required')
            
            # Redirection vers le dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:dashboard')
        else:
            # Mot de passe incorrect
            audit_login_failed(request, username)
            
            # Enregistrer la tentative échouée
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                successful=False
            )
            
            # Incrémenter les compteurs
            user_attempts += 1
            remaining_after = MAX_ATTEMPTS - user_attempts
            
            if remaining_after <= 0:
                # Verrouiller maintenant
                cache_data = {
                    'attempts': user_attempts,
                    'lock_time': timezone.now()
                }
                error_message = f'🔒 Mot de passe incorrect ! Compte bloqué pendant {LOCKOUT_DURATION//60} minutes.'
            else:
                cache_data = {'attempts': user_attempts, 'lock_time': None}
                error_message = f'🔒 Mot de passe incorrect ! Il vous reste {remaining_after} tentative(s).'
            
            cache.set(user_key, cache_data, LOCKOUT_DURATION)
            
            return render(request, 'login.html', {
                'error': error_message,
                'remaining_attempts': remaining_after,
                'form': {
                    'username': {'value': username},
                    'password': {'value': ''}
                },
                'wrong_password': True
            })
    
    # GET request - afficher le formulaire vide
    return render(request, 'login.html', {
        'remaining_attempts': MAX_ATTEMPTS,
        'form': {
            'username': {'value': ''},
            'password': {'value': ''}
        }
    })
 
 
@require_POST
def update_activity(request):
    """
    SEULE vue autorisée à mettre à jour last_activity
    Appelée uniquement via AJAX
    """
    if request.user.is_authenticated:
        request.session['last_activity'] = timezone.now().isoformat()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=401)

# accounts/views.py - AJOUTER
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def debug_session(request):
    """Vue de debug pour vérifier l'état de la session"""
    if request.user.is_authenticated:
        data = {
            'authenticated': True,
            'session_data': dict(request.session),
            'show_warning': request.session.get('show_warning', False),
            'warning_time': request.session.get('warning_time', 0),
            'remaining_time': request.session.get('remaining_time', 300),
            'last_activity': request.session.get('last_activity'),
        }
        
        response = JsonResponse(data)
        
        # Ajouter les headers pour le JavaScript
        response['X-Session-Remaining'] = str(request.session.get('remaining_time', 300))
        response['X-Session-Warning'] = 'true' if request.session.get('show_warning') else 'false'
        
        return response
    
    return JsonResponse({'authenticated': False}, status=401)

# def login_view(request):
#     """Vue de connexion avec validation en temps réel et protection contre les attaques"""
    
#     # Configuration de sécurité
#     MAX_ATTEMPTS = 5
#     LOCKOUT_DURATION = 900  # 15 minutes
    
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         # Validation basique
#         if not username or not password:
#             return render(request, 'login.html', {
#                 'error': 'Veuillez remplir tous les champs',
#                 'remaining_attempts': MAX_ATTEMPTS,
#                 'form': {
#                     'username': {'value': username or ''},
#                     'password': {'value': ''}
#                 }
#             })
        
#         # Vérifier si l'utilisateur/IP est bloqué(e)
#         from .middleware import get_client_ip
#         ip_address = get_client_ip(request)
        
#         # Clés pour le cache
#         #ip_key = f"login_attempts_ip_{ip_address}"
#         user_key = f"login_attempts_user_{username}"
        
#         # Vérifier les tentatives
#         #ip_attempts = cache.get(ip_key, 0)
#         user_attempts = cache.get(user_key, 0)
        
#         # Calculer les tentatives restantes AVANT la nouvelle tentative
#         remaining_before = MAX_ATTEMPTS - user_attempts
        
#         #if ip_attempts >= MAX_ATTEMPTS or user_attempts >= MAX_ATTEMPTS:
#         if user_attempts >= MAX_ATTEMPTS:
#             # Enregistrer la tentative bloquée
#             from .models import LoginAttempt
#             LoginAttempt.objects.create(
#                 username=username,
#                 ip_address=ip_address,
#                 successful=False
#             )
            
#             audit_login_failed(request, username)
            
#             return render(request, 'login.html', {
#                 'error': f'⛔ Trop de tentatives de connexion. Veuillez réessayer dans {LOCKOUT_DURATION//60} minutes.',
#                 'remaining_attempts': 0,
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 }
#             })
        
#         # CHERCHEZ L'UTILISATEUR (sans élever d'exception)
#         user = None
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             # AUDIT: Tentative avec nom d'utilisateur inexistant
#             audit_login_failed(request, username)
#             # Cherchez aussi par email si votre système le permet
#             try:
#                 user = User.objects.get(email=username)
#             except (User.DoesNotExist, User.MultipleObjectsReturned):
#                 pass
        
#         if user is None:
#             # Utilisateur n'existe pas
#             audit_login_failed(request, username)
            
#             # Enregistrer la tentative et incrémenter les compteurs
#             from .models import LoginAttempt
#             LoginAttempt.objects.create(
#                 username=username,
#                 ip_address=ip_address,
#                 successful=False
#             )
            
#             #cache.set(ip_key, ip_attempts + 1, LOCKOUT_DURATION)
#             cache.set(user_key, user_attempts + 1, LOCKOUT_DURATION)
            
#             remaining_after = MAX_ATTEMPTS - (user_attempts + 1)  # Après l'incrémentation
#             error_msg = 'Nom d\'utilisateur non reconnu'
#             if remaining_after > 0:
#                 error_msg += f'. Il vous reste {remaining_after} tentative(s).'
#             else:
#                 error_msg += f'. Compte bloqué pendant {LOCKOUT_DURATION//60} minutes.'
            
#             return render(request, 'login.html', {
#                 'error': error_msg,
#                 'remaining_attempts': remaining_after,
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 }
#             })
        
#         # VÉRIFIEZ L'ÉTAT DU COMPTE
#         if not user.is_active:
#             # Compte désactivé - message précis
#             audit_login_failed(request, username)
            
#             from .models import LoginAttempt
#             LoginAttempt.objects.create(
#                 username=username,
#                 ip_address=ip_address,
#                 successful=False
#             )
            
#             #cache.set(ip_key, ip_attempts + 1, LOCKOUT_DURATION)
#             cache.set(user_key, user_attempts + 1, LOCKOUT_DURATION)
            
#             remaining_after = MAX_ATTEMPTS - (user_attempts + 1)
            
#             return render(request, 'login.html', {
#                 'error': '❌ <strong>Compte désactivé</strong><br>Votre compte a été désactivé par l\'administration. Veuillez contacter le support technique.',
#                 'remaining_attempts': remaining_after,
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 },
#                 'account_disabled': True
#             })
        
#         # TENTATIVE D'AUTHENTIFICATION
#         auth_user = authenticate(request, username=user.username, password=password)
        
#         if auth_user:
#             # Connexion réussie - réinitialiser les compteurs
#             #cache.delete(ip_key)
#             cache.delete(user_key)
            
#             # Enregistrer la tentative réussie
#             from .models import LoginAttempt
#             LoginAttempt.objects.create(
#                 username=username,
#                 ip_address=ip_address,
#                 successful=True
#             )
            
#             login(request, auth_user)
#             # ✅ AUDIT: Connexion réussie
#             audit_login(request, auth_user)
            
#             # Définir le timestamp de dernière activité
#             request.session['last_activity'] = timezone.now().isoformat()
            
#             # Vérifier si premier login
#             if hasattr(auth_user, 'first_login') and auth_user.first_login:
#                 messages.info(request, "Veuillez changer votre mot de passe pour la première connexion.")
#                 return redirect('accounts:change_password_required')
            
#             # Redirection vers le dashboard
#             next_url = request.GET.get('next')
#             if next_url:
#                 return redirect(next_url)
#             return redirect('accounts:dashboard')
#         else:
#             # Mot de passe incorrect
#             audit_login_failed(request, username)
            
#             # Enregistrer la tentative échouée
#             from .models import LoginAttempt
#             LoginAttempt.objects.create(
#                 username=username,
#                 ip_address=ip_address,
#                 successful=False
#             )
            
#             # Incrémenter les compteurs
#             remaining_after = MAX_ATTEMPTS - (user_attempts + 1)  # Après l'incrémentation
#             #cache.set(ip_key, ip_attempts + 1, LOCKOUT_DURATION)
#             cache.set(user_key, user_attempts + 1, LOCKOUT_DURATION)
            
#             error_message = '🔒 Mot de passe incorrect !'
#             if remaining_after > 0:
#                 error_message += f' Il vous reste {remaining_after} tentative(s).'
#             else:
#                 error_message += f' Compte bloqué pendant {LOCKOUT_DURATION//60} minutes.'
            
#             return render(request, 'login.html', {
#                 'error': error_message,
#                 'remaining_attempts': remaining_after,
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 },
#                 'wrong_password': True
#             })
    
#     # GET request - afficher le formulaire vide
#     return render(request, 'login.html', {
#         'remaining_attempts': MAX_ATTEMPTS,
#         'form': {
#             'username': {'value': ''},
#             'password': {'value': ''}
#         }
#     })

def login_attempts_view(request):
    """Vue pour afficher les tentatives de connexion (admin seulement)"""
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('accounts:login')
    
    # Filtres
    date_filter = request.GET.get('date', '')
    username_filter = request.GET.get('username', '')
    ip_filter = request.GET.get('ip', '')
    status_filter = request.GET.get('status', '')
    
    attempts = LoginAttempt.objects.all().order_by('-timestamp')
    
    # Appliquer les filtres
    if date_filter:
        if date_filter == 'today':
            today = timezone.now().date()
            attempts = attempts.filter(timestamp__date=today)
        elif date_filter == 'yesterday':
            yesterday = timezone.now().date() - timezone.timedelta(days=1)
            attempts = attempts.filter(timestamp__date=yesterday)
        elif date_filter == 'week':
            week_ago = timezone.now() - timezone.timedelta(days=7)
            attempts = attempts.filter(timestamp__gte=week_ago)
    
    if username_filter:
        attempts = attempts.filter(username__icontains=username_filter)
    
    if ip_filter:
        attempts = attempts.filter(ip_address__icontains=ip_filter)
    
    if status_filter:
        if status_filter == 'success':
            attempts = attempts.filter(successful=True)
        elif status_filter == 'failed':
            attempts = attempts.filter(successful=False)
    
    # Statistiques
    total = attempts.count()
    successful = attempts.filter(successful=True).count()
    failed = attempts.filter(successful=False).count()
    
    # Pagination
    paginator = Paginator(attempts, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total': total,
        'successful': successful,
        'failed': failed,
        'filters': {
            'date': date_filter,
            'username': username_filter,
            'ip': ip_filter,
            'status': status_filter,
        }
    }
    
    return render(request, 'accounts/login_attempts.html', context)

# def login_view(request):
#     """Vue de connexion avec validation en temps réel"""
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         # Validation basique
#         if not username or not password:
#             return render(request, 'login.html', {
#                 'error': 'Veuillez remplir tous les champs',
#                 'form': {
#                     'username': {'value': username or ''},
#                     'password': {'value': ''}
#                 }
#             })
        
#         # CHERCHEZ L'UTILISATEUR (sans élever d'exception)
#         user = None
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             # AUDIT: Tentative avec nom d'utilisateur inexistant
#             audit_login_failed(request, username)
#             # Cherchez aussi par email si votre système le permet
#             try:
#                 user = User.objects.get(email=username)
#             except (User.DoesNotExist, User.MultipleObjectsReturned):
#                 pass
        
#         if user is None:
#             # Utilisateur n'existe pas
#             # AUDIT: Utilisateur non trouvé
#             audit_login_failed(request, username)

#             return render(request, 'login.html', {
#                 'error': 'Nom d\'utilisateur non reconnu',
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 }
#             })
        
#         # VÉRIFIEZ L'ÉTAT DU COMPTE
#         if not user.is_active:
#             # Compte désactivé - message précis
#             # AUDIT: Tentative sur compte désactivé
#             audit_login_failed(request, username)
#             return render(request, 'login.html', {
#                 'error': '❌ <strong>Compte désactivé</strong><br>Votre compte a été désactivé par l\'administration. Veuillez contacter le support technique.',
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 },
#                 'account_disabled': True
#             })
        
#         # TENTATIVE D'AUTHENTIFICATION
#         auth_user = authenticate(request, username=user.username, password=password)
        
#         if auth_user:
#             # Connexion réussie
#             login(request, auth_user)
#             # ✅ AUDIT: Connexion réussie
#             audit_login(request, auth_user)
            
#             # Vérifier si premier login
#             if hasattr(auth_user, 'first_login') and auth_user.first_login:
#                 messages.info(request, "Veuillez changer votre mot de passe pour la première connexion.")
#                 return redirect('accounts:change_password_required')
            
#             # Redirection vers le dashboard
#             next_url = request.GET.get('next')
#             if next_url:
#                 return redirect(next_url)
#             return redirect('accounts:dashboard')
#         else:
#             # Mot de passe incorrect
#              # AUDIT: Mot de passe incorrect
#             audit_login_failed(request, username)
#             return render(request, 'login.html', {
#                 'error': '🔒 Mot de passe incorrect ! Vérifiez votre mot de passe et réessayez.',
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 },
#                 'wrong_password': True
#             })
    
#     # GET request - afficher le formulaire vide
#     return render(request, 'login.html', {
#         'form': {
#             'username': {'value': ''},
#             'password': {'value': ''}
#         }
#     })


# def login_view(request):
#     """Vue de connexion avec validation en temps réel"""
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         # Validation basique
#         if not username or not password:
#             return render(request, 'login.html', {
#                 'error': 'Veuillez remplir tous les champs',
#                 'form': {
#                     'username': {'value': username or ''},
#                     'password': {'value': ''}
#                 }
#             })
        
#         # Tentative d'authentification
#         user = authenticate(request, username=username, password=password)
        
#         if user:
#             if user.is_active:
#                 login(request, user)
                
#                 # Vérifier si premier login
#                 if hasattr(user, 'first_login') and user.first_login:
#                     messages.info(request, "Veuillez changer votre mot de passe pour la première connexion.")
#                     return redirect('accounts:change_password_required')
                
#                 # Redirection vers le dashboard
#                 next_url = request.GET.get('next')
#                 if next_url:
#                     return redirect(next_url)
#                 return redirect('accounts:dashboard')
#             else:
#                 return render(request, 'login.html', {
#                     'error': 'Ce compte est désactivé. Veuillez contacter l\'administration.',
#                     'error_type': 'account_disabled',  # AJOUTEZ CE CHAMP
#                     'form': {
#                         'username': {'value': username},
#                         'password': {'value': ''}
#                     },
#                     'account_disabled': True 
#                 })
#         else:
#             return render(request, 'login.html', {
#                 'error': 'Nom d\'utilisateur ou mot de passe incorrect',
#                 'error_type': 'auth_failed',  # AJOUTEZ CE CHAMP
#                 'form': {
#                     'username': {'value': username},
#                     'password': {'value': ''}
#                 }
#             })
    
#     # GET request - afficher le formulaire vide
#     return render(request, 'login.html', {
#         'form': {
#             'username': {'value': ''},
#             'password': {'value': ''}
#         }
#     })


@login_required
def change_password_required(request):
    if not request.user.first_login:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.first_login = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe changé avec succès!")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password_required.html', {'form': form})

@require_http_methods(["POST"])
@login_required
def logout_view(request):
    # ✅ AUDIT: Déconnexion
    audit_logout(request, request.user)
    
    logout(request)
    return redirect('accounts:login')

@login_required
def logout_confirm(request):
    return render(request, 'accounts/logout_confirm.html')
 


@login_required
@permission_required(can_manage_admins, redirect_url='accounts:dashboard')
def creer_admin(request):
    """
    Vue optimisée pour la création d'un administrateur.
    Même workflow que pour les professeurs.
    """
    form = AdminCreationForm(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                # 🔒 DÉBUT DE LA TRANSACTION ATOMIQUE
                with transaction.atomic():
                    # 🔇 DÉSACTIVER TEMPORAIREMENT LE SIGNAL
                    signals.post_save.disconnect(create_user_profile, sender=User)
                    
                    # 👤 CRÉATION DE L'UTILISATEUR
                    user = form.save(commit=False)
                    user.role = User.Role.ADMIN
                    user.first_login = True
                    
                    # 🔑 MOT DE PASSE PAR DÉFAUT (fixe)
                    user.set_password("1234")
                    user.save()
                    
                    # 👨‍💼 CRÉATION DU PROFIL ADMIN
                    niveau_acces = form.cleaned_data['niveau_acces']
                    
                    # Définir les permissions selon le niveau
                    permissions = {
                        'niveau_acces': niveau_acces,
                        'peut_gerer_utilisateurs': True,
                        'peut_gerer_cours': True,
                        'peut_valider_notes': True,
                        'peut_gerer_facultes': True,
                    }
                    
                    # Ajuster selon le niveau
                    if niveau_acces == 'academique':
                        permissions['peut_gerer_utilisateurs'] = False
                    elif niveau_acces == 'utilisateurs':
                        permissions.update({
                            'peut_gerer_cours': False,
                            'peut_valider_notes': False,
                            'peut_gerer_facultes': False,
                        })
                    
                    admin = Admin.objects.create(
                        user=user,
                        **permissions
                    )
                    
                    # 🔊 RÉACTIVER LE SIGNAL
                    signals.post_save.connect(create_user_profile, sender=User)
                
                # ✅ SUCCÈS - MESSAGE ET REDIRECTION
                full_name = user.get_full_name() or user.username
                
                # ✅ AUDIT: Création réussie
                audit_creer_admin(request, admin)
                
                messages.success(
                    request, 
                    f"✅ Administrateur <strong>{full_name}</strong> créé avec succès !<br>"
                    f"<strong>Nom d'utilisateur:</strong> {user.username}<br>"
                    f"<strong>Mot de passe:</strong> 1234<br>"
                    f"<strong>Niveau d'accès:</strong> {admin.get_niveau_acces_display()}"
                )
                
                # 📊 LOG SUCCÈS (optionnel)
                print(f"✅ ADMIN CRÉÉ: {user.username} ({user.email}) - Niveau: {niveau_acces}")
                
                return redirect('accounts:liste_admins')

            except IntegrityError as e:
                # 🔊 RÉACTIVER LE SIGNAL EN CAS D'ERREUR
                signals.post_save.connect(create_user_profile, sender=User)
                
                # 🚨 GESTION DES ERREURS D'INTÉGRITÉ SPÉCIFIQUES
                error_msg = str(e)
                if 'username' in error_msg.lower():
                    messages.error(request, "❌ Ce nom d'utilisateur est déjà utilisé.")
                elif 'email' in error_msg.lower():
                    messages.error(request, "❌ Cette adresse email est déjà utilisée.")
                elif 'unique' in error_msg.lower():
                    messages.error(request, "❌ Violation de contrainte d'unicité.")
                else:
                    messages.error(request, f"❌ Erreur d'intégrité : {error_msg}")
                
                # 🗑️ NETTOYAGE SI UTILISATEUR CRÉÉ
                if 'user' in locals() and hasattr(user, 'pk') and user.pk:
                    user.delete(force_policy=True)
                    
            except Exception as e:
                # 🔊 RÉACTIVER LE SIGNAL EN CAS D'ERREUR GÉNÉRIQUE
                signals.post_save.connect(create_user_profile, sender=User)
                
                # 🚨 GESTION DES ERREURS GÉNÉRIQUES
                error_type = type(e).__name__
                messages.error(
                    request, 
                    f"❌ Erreur [{error_type}] : {str(e)[:100]}..."
                )
                
                # 🗑️ NETTOYAGE SI UTILISATEUR CRÉÉ
                if 'user' in locals() and hasattr(user, 'pk') and user.pk:
                    try:
                        user.delete(force_policy=True)
                    except:
                        pass
                        
                # 📋 LOG ERREUR
                print(f"❌ ERREUR CRÉATION ADMIN: {error_type} - {e}")
                
        else:
            # 📝 VALIDATION DES FORMULAIRES ÉCHOUÉE
            error_count = len(form.errors)
            messages.error(
                request, 
                f"❌ Validation échouée ({error_count} erreur{'s' if error_count > 1 else ''}). "
                "Veuillez corriger les champs marqués en rouge."
            )
            
            # 🎯 AJOUT DES CLASSES D'ERREUR AUX CHAMPS
            for field in form:
                if field.errors:
                    field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' is-invalid'

    # 🎨 RENDU DU TEMPLATE
    context = {
        'form': form,
        'page_title': 'Créer un Administrateur',
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': 'accounts:dashboard'},
            {'name': 'Administrateurs', 'url': 'accounts:liste_admins'},
            {'name': 'Créer', 'url': 'accounts:creer_admin'},
        ]
    }
    
    return render(request, 'accounts/creer_admin.html', context)


@login_required
@permission_required(can_manage_admins, redirect_url='accounts:dashboard')
def liste_admins(request):
    """Affiche la liste des administrateurs"""
    admins = Admin.objects.select_related('user').all().order_by('-date_nomination')
    
    context = {
        'admins': admins,
        'page_title': 'Liste des Administrateurs'
    }
    
    return render(request, 'accounts/liste_admins.html', context)

 
# accounts/views.py
@login_required
@django_superuser_required  # <-- NOUVEAU décorateur
def creer_admin_systeme(request):
    """
    Vue accessible UNIQUEMENT au superuser Django
    Permet de créer un administrateur avec niveau d'accès
    """
    form = AdminCreationForm(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 🔇 Désactiver temporairement le signal
                    post_save.disconnect(create_user_profile, sender=User)
                    
                    # Créer l'utilisateur
                    user = form.save(commit=False)
                    user.role = User.Role.ADMIN  # Rôle ADMIN
                    user.first_login = True
                    user.set_password("1234")  # Mot de passe par défaut
                    user.save()
                    
                    # Créer le profil Admin
                    niveau_acces = form.cleaned_data['niveau_acces']
                    
                    # Définir les permissions selon le niveau
                    permissions = {
                        'niveau_acces': niveau_acces,
                        'peut_gerer_utilisateurs': True,
                        'peut_gerer_cours': True,
                        'peut_valider_notes': True,
                        'peut_gerer_facultes': True,
                    }
                    
                    # Ajuster selon le niveau
                    if niveau_acces == 'academique':
                        permissions['peut_gerer_utilisateurs'] = False
                    elif niveau_acces == 'utilisateurs':
                        permissions.update({
                            'peut_gerer_cours': False,
                            'peut_valider_notes': False,
                            'peut_gerer_facultes': False,
                        })
                    
                    admin = Admin.objects.create(
                        user=user,
                        **permissions
                    )
                    
                    # 🔊 Réactiver le signal
                    post_save.connect(create_user_profile, sender=User)
                
                # ✅ Succès
                messages.success(request, 
                    f"✅ Administrateur {user.get_full_name()} créé avec succès!<br>"
                    f"<strong>Nom d'utilisateur:</strong> {user.username}<br>"
                    f"<strong>Mot de passe temporaire:</strong> 1234"
                )
                
                # Audit
                audit_creer_admin(request, admin)
                
                return redirect('accounts:liste_admins_systeme')
                
            except Exception as e:
                post_save.connect(create_user_profile, sender=User)
                messages.error(request, f"❌ Erreur: {str(e)}")
    
    return render(request, 'accounts/creer_admin_systeme.html', {
        'form': form,
        'is_django_superuser': True
    }) 
 
# accounts/views.py
@login_required
@django_superuser_required
def liste_admins_systeme(request):
    """Liste de tous les administrateurs (superuser seulement)"""
    admins = Admin.objects.select_related('user').all().order_by('-date_nomination')
    
    return render(request, 'accounts/liste_admins_systeme.html', {
        'admins': admins,
        'is_django_superuser': True
    }) 
 

@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def creer_etudiant(request):
    # DÉSACTIVER le signal au tout début
    post_save.disconnect(create_user_profile, sender=User)
    
    user_form = UserForm(request.POST or None)
    etu_form = EtudiantForm(request.POST or None)
    
    try:
        if request.method == 'POST':
            # Debug simplifié
            print(f"=== CRÉATION ÉTUDIANT ===")
            print(f"Forms valides: User={user_form.is_valid()}, Etu={etu_form.is_valid()}")
            
            if user_form.is_valid() and etu_form.is_valid():
                try:
                    # Vérifications préliminaires
                    username = user_form.cleaned_data['username']
                    email = user_form.cleaned_data['email']
                    # Appliquer les valeurs automatiques
                    etudiant = etu_form.save(commit=False)
                    etudiant.annee_academique_courante = get_annee_academique()
                    etudiant.statut_academique = 'actif'
                    
                    if User.objects.filter(username=username).exists():
                        messages.error(request, f"Le nom d'utilisateur '{username}' est déjà utilisé.")
                        return render(request, 'accounts/creer_etudiant.html', {
                            'user_form': user_form,
                            'etu_form': etu_form,
                            'form_invalid': True
                        })
                    
                    if User.objects.filter(email=email).exists():
                        messages.error(request, f"L'email '{email}' est déjà utilisé.")
                        return render(request, 'accounts/creer_etudiant.html', {
                            'user_form': user_form,
                            'etu_form': etu_form,
                            'form_invalid': True
                        })
                    
                    # TRANSACTION ATOMIQUE - Tout ou rien
                    with transaction.atomic():
                        # 1. Créer l'utilisateur
                        user = user_form.save(commit=False)
                        user.role = User.Role.ETUDIANT
                        user.first_login = True
                        user.set_password("1234")
                        user.save()
                        print(f"✅ User créé: {user.username} (ID:{user.id})")
                        
                        # 2. Créer l'étudiant avec matricule
                        etudiant = etu_form.save(commit=False)
                        etudiant.user = user
                        
                        # Générer matricule unique
                        annee = timezone.now().year
                        faculte_code = etudiant.faculte.code[:3].upper() if etudiant.faculte.code else "ETU"
                        
                        # Trouver le prochain numéro
                        dernier = Etudiant.objects.filter(
                            matricule__startswith=f"{annee}-{faculte_code}-"
                        ).order_by('-matricule').first()
                        
                        if dernier:
                            try:
                                dernier_num = int(dernier.matricule.split('-')[-1])
                                nouveau_num = dernier_num + 1
                            except (ValueError, IndexError):
                                nouveau_num = 1
                        else:
                            nouveau_num = 1
                        
                        etudiant.matricule = f"{annee}-{faculte_code}-{nouveau_num:04d}"
                        etudiant.save()
                        print(f"✅ Étudiant créé: {etudiant.matricule}")
                        
                        # 3. Attribution des cours (si nécessaire)
                        try:
                            from grades.models import InscriptionCours
                            from academics.models import Cours
                            
                            # mois = timezone.now().month
                            # semestre = 'S1' if (9 <= mois <= 12 or mois == 1) else 'S2'
                            semestre = etudiant.semestre_courant
                            cours_disponibles = Cours.objects.filter(
                                faculte=etudiant.faculte,
                                niveau=etudiant.niveau,
                                semestre=semestre
                            )
                            
                            for cours in cours_disponibles:
                                InscriptionCours.objects.get_or_create(
                                    etudiant=etudiant,
                                    cours=cours
                                )
                            print(f"📚 {cours_disponibles.count()} cours attribués")
                        except Exception as e:
                            print(f"⚠️ Cours non attribués: {e}")
                    # ✅ AUDIT: Création réussie
                    audit_creer_etudiant(request, etudiant)
                    # SUCCÈS - Réactiver le signal avant redirection
                    post_save.connect(create_user_profile, sender=User)
                    messages.success(request, f"✅ Étudiant {user.get_full_name()} créé avec succès !")
                    return redirect('accounts:liste_etudiants')
                    
                except Exception as e:
                    # AUDIT: Échec de création
                    audit_action_generique(request, 'CREATE_STUDENT_FAILED', 
                                          f"Étudiant (erreur)", 
                                          f"Erreur création étudiant: {str(e)[:100]}")
                    
                    print(f"❌ Erreur création: {str(e)}")
                    messages.error(request, f"Erreur: {str(e)}")
            
            else:
                # Affichage des erreurs de formulaire
                if not user_form.is_valid():
                    for field, errors in user_form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                
                if not etu_form.is_valid():
                    for field, errors in etu_form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
    
    except Exception as e:
        print(f"❌ Erreur globale: {str(e)}")
        messages.error(request, f"Erreur système: {str(e)}")
    
    finally:
        # TOUJOURS réactiver le signal, même en cas d'erreur
        try:
            # Vérifier si le signal n'est pas déjà connecté
            receivers = post_save._live_receivers(User)
            signal_connected = False
            
            for receiver in receivers:
                # Vérification sécurisée
                try:
                    if hasattr(receiver, '__name__') and receiver.__name__ == 'create_user_profile':
                        signal_connected = True
                        break
                except:
                    continue
            
            if not signal_connected:
                post_save.connect(create_user_profile, sender=User)
                print("✅ Signal réactivé")
        except Exception as e:
            print(f"⚠️ Erreur réactivation signal: {e}")
            # Tentative de réactivation malgré l'erreur
            try:
                post_save.connect(create_user_profile, sender=User)
            except:
                pass
    
    # Rendu du template (GET ou POST avec erreurs)
    return render(request, 'accounts/creer_etudiant.html', {
        'user_form': user_form,
        'etu_form': etu_form,
        'form_invalid': request.method == 'POST'
    })



@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def creer_professeur(request):
    """
    Vue optimisée pour la création d'un professeur.
    Gestion robuste des transactions, signaux et erreurs.
    """
    user_form = UserForm(request.POST or None)
    prof_form = ProfesseurForm(request.POST or None)

    if request.method == 'POST':
        if user_form.is_valid() and prof_form.is_valid():
            try:
                # 🔒 DÉBUT DE LA TRANSACTION ATOMIQUE
                with transaction.atomic():
                    # 🔇 DÉSACTIVER TEMPORAIREMENT LE SIGNAL
                    signals.post_save.disconnect(create_user_profile, sender=User)
                    
                    # 👤 CRÉATION DE L'UTILISATEUR
                    user = user_form.save(commit=False)
                    user.role = User.Role.PROFESSEUR
                    user.first_login = True
                    
                    # 🔑 MOT DE PASSE PAR DÉFAUT (fixe)
                    user.set_password("1234")
                    user.save()
                    
                    # 👨‍🏫 CRÉATION DU PROFIL PROFESSEUR
                    professeur = prof_form.save(commit=False)
                    professeur.user = user
                    professeur.save()
                    
                    # 🔊 RÉACTIVER LE SIGNAL
                    signals.post_save.connect(create_user_profile, sender=User)
                
                # ✅ SUCCÈS - MESSAGE ET REDIRECTION
                full_name = user.get_full_name() or user.username
                # ✅ AUDIT: Création réussie
                audit_creer_professeur(request, professeur)
                messages.success(
                    request, 
                    f"✅ Professeur <strong>{full_name}</strong> créé avec succès ! "
                    f"(Matricule: {user.username}, Mot de passe: 1234)"
                )
                
                # 📊 LOG SUCCÈS (optionnel)
                print(f"✅ PROFESSEUR CRÉÉ: {user.username} ({user.email})")
                
                return redirect('accounts:liste_professeurs')

            except IntegrityError as e:
                # AUDIT: Échec de création
                audit_action_generique(request, 'CREATE_TEACHER_FAILED', 
                                      f"Professeur (erreur)", 
                                      f"Erreur création professeur: {str(e)[:100]}")
                # 🔄 RÉACTIVER LE SIGNAL EN CAS D'ERREUR
                signals.post_save.connect(create_user_profile, sender=User)
                
                # 🚨 GESTION DES ERREURS D'INTÉGRITÉ SPÉCIFIQUES
                error_msg = str(e)
                if 'username' in error_msg.lower():
                    messages.error(request, "❌ Ce nom d'utilisateur est déjà utilisé.")
                elif 'email' in error_msg.lower():
                    messages.error(request, "❌ Cette adresse email est déjà utilisée.")
                elif 'unique' in error_msg.lower():
                    messages.error(request, "❌ Violation de contrainte d'unicité.")
                else:
                    messages.error(request, f"❌ Erreur d'intégrité : {error_msg}")
                
                # 🗑️ NETTOYAGE SI UTILISATEUR CRÉÉ
                if 'user' in locals() and hasattr(user, 'pk') and user.pk:
                    user.delete(force_policy=True)
                    
            except Exception as e:
                # 🔄 RÉACTIVER LE SIGNAL EN CAS D'ERREUR GÉNÉRIQUE
                signals.post_save.connect(create_user_profile, sender=User)
                
                # 🚨 GESTION DES ERREURS GÉNÉRIQUES
                error_type = type(e).__name__
                messages.error(
                    request, 
                    f"❌ Erreur [{error_type}] : {str(e)[:100]}..."
                )
                
                # 🗑️ NETTOYAGE SI UTILISATEUR CRÉÉ
                if 'user' in locals() and hasattr(user, 'pk') and user.pk:
                    try:
                        user.delete(force_policy=True)
                    except:
                        pass
                        
                # 📋 LOG ERREUR
                print(f"❌ ERREUR CRÉATION PROFESSEUR: {error_type} - {e}")
                
        else:
            # 📝 VALIDATION DES FORMULAIRES ÉCHOUÉE
            error_count = len(user_form.errors) + len(prof_form.errors)
            messages.error(
                request, 
                f"❌ Validation échouée ({error_count} erreur{'s' if error_count > 1 else ''}). "
                "Veuillez corriger les champs marqués en rouge."
            )
            
            # 🎯 AJOUT DES CLASSES D'ERREUR AUX CHAMPS
            for field in user_form:
                if field.errors:
                    field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' is-invalid'
            
            for field in prof_form:
                if field.errors:
                    field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' is-invalid'

    # 🎨 RENDU DU TEMPLATE
    context = {
        'user_form': user_form,
        'prof_form': prof_form,
        'page_title': 'Créer un Professeur',
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': 'accounts:dashboard'},
            {'name': 'Professeurs', 'url': 'accounts:liste_professeurs'},
            {'name': 'Créer', 'url': 'accounts:creer_professeur'},
        ]
    }
    
    return render(request, 'accounts/creer_professeur.html', context)


# @login_required
# @user_passes_test(can_manage_users)
# def creer_professeur(request):
#     user_form = UserForm(request.POST or None)
#     prof_form = ProfesseurForm(request.POST or None)

#     if request.method == 'POST':
#         if user_form.is_valid() and prof_form.is_valid():
#             try:
#                 # ✅ DÉSACTIVER le signal temporairement
#                 from django.db.models import signals
#                 from .signals import create_user_profile
#                 signals.post_save.disconnect(create_user_profile, sender=User)
                
#                 user = user_form.save(commit=False)
#                 user.role = User.Role.PROFESSEUR
#                 user.first_login = True

#                 password = user_form.cleaned_data.get('password')
#                 if password:
#                     user.set_password(password)
#                 else:
#                     messages.error(request, "Le mot de passe est obligatoire.")
#                     # ✅ RÉACTIVER le signal avant de retourner
#                     signals.post_save.connect(create_user_profile, sender=User)
#                     return render(request, 'accounts/creer_professeur.html', {
#                         'user_form': user_form,
#                         'prof_form': prof_form,
#                     })

#                 user.save()

#                 # ✅ Maintenant créer le profil Professeur manuellement
#                 # (le signal ne s'est pas déclenché)
#                 professeur = prof_form.save(commit=False)
#                 professeur.user = user
#                 professeur.save()
                
#                 messages.success(request, "Professeur créé avec succès")
                
#                 # ✅ RÉACTIVER le signal
#                 signals.post_save.connect(create_user_profile, sender=User)
#                 return redirect('accounts:liste_professeurs')

#             except IntegrityError as e:
#                 # ✅ RÉACTIVER le signal en cas d'erreur
#                 signals.post_save.connect(create_user_profile, sender=User)
#                 messages.error(request, f"Erreur lors de la création : {e}")
#                 if 'user' in locals() and user.pk:
#                     user.delete()
#             except Exception as e:
#                 # ✅ RÉACTIVER le signal en cas d'erreur
#                 signals.post_save.connect(create_user_profile, sender=User)
#                 messages.error(request, f"Erreur inattendue : {e}")
#                 if 'user' in locals() and user.pk:
#                     user.delete()
#         else:
#             messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
#     else:
#         user_form = UserForm()
#         prof_form = ProfesseurForm()

#     return render(request, 'accounts/creer_professeur.html', {
#         'user_form': user_form,
#         'prof_form': prof_form,
#     })


@login_required
def dashboard(request):
    user = request.user

    is_django_superuser = user.is_superuser
    
    if user.role == User.Role.ADMIN or is_django_superuser:
        from academics.models import Faculte, Cours
        from grades.models import Note
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q
        
        # Statistiques de base
        stats = {
            'etudiants': Etudiant.objects.count(),
            'professeurs': Professeur.objects.count(),
            'facultes': Faculte.objects.count(),
            'cours': Cours.objects.count(),
            'admins': Admin.objects.count(),
        }
        
        # Données supplémentaires pour le dashboard
        notes_soumises = Note.objects.filter(statut='soumise') 

        # STATISTIQUES SYSTÈME POUR ADMIN SEULEMENT
        maintenant = timezone.now()
        date_limite_24h = maintenant - timedelta(hours=24)
        date_limite_30j = maintenant - timedelta(days=30)
 
        
        # DEBUG: Afficher les dates pour vérifier
        print(f"DEBUG - Maintenant: {maintenant}")
        print(f"DEBUG - Limite 24h: {date_limite_24h}")

        
        # Connexions récentes (dernières 24h)
        connexions_recentes = User.objects.filter(
            last_login__gte=date_limite_24h
        ).count()
        print(f'le voici: {connexions_recentes}')
        
        
        # Comptes actifs (connectés dans les 30 derniers jours)
        comptes_actifs = User.objects.filter(
            last_login__gte=date_limite_30j
        ).count()
        
        # Comptes inactifs (pas connectés depuis 30+ jours)
        comptes_inactifs = User.objects.filter(
            Q(last_login__lt=date_limite_30j) | Q(last_login__isnull=True)
        ).count()
        
        # AJOUTEZ CE CALCUL POUR LES COMPTES DÉSACTIVÉS
        comptes_desactives = User.objects.filter(
            is_active=False
        ).count()
        # Total utilisateurs
        total_utilisateurs = User.objects.count()
        
        # Pourcentage d'activité
        pourcentage_actif = (comptes_actifs / total_utilisateurs * 100) if total_utilisateurs > 0 else 0
        
        context = {
            'role': 'admin',
            'stats': stats,
            'notes_soumises': notes_soumises, 
            'connexions_recentes': connexions_recentes,
            'comptes_actifs': comptes_actifs,
            'comptes_inactifs': comptes_inactifs,
            'comptes_desactives': comptes_desactives,
            'total_utilisateurs': total_utilisateurs,
            'pourcentage_actif': round(pourcentage_actif, 1),
            'is_django_superuser': is_django_superuser,
        }
    
    elif user.role == User.Role.PROFESSEUR:
        from academics.models import Cours
        from django.db.models import Count, Exists, OuterRef, Subquery
        from grades.models import InscriptionCours
        
        # OPTION A: Annotation avec COUNT des inscriptions
        cours_assignes = Cours.objects.filter(
            professeur=user
        ).annotate(
            nb_etudiants_inscrits=Count('inscriptions', distinct=True)
        ).select_related('faculte')
        
        # OPTION B: Annotation avec SUBQUERY (plus performant pour les grandes BDD)
        cours_assignes = Cours.objects.filter(
            professeur=user
        ).annotate(
            nb_inscrits=Subquery(
                InscriptionCours.objects.filter(
                    cours=OuterRef('pk')
                ).values('cours')
                .annotate(count=Count('*'))
                .values('count')[:1]
            )
        ).select_related('faculte')
        
        # Pour chaque cours, afficher aussi le nombre d'étudiants concernés
        for cours in cours_assignes:
            cours.nb_concernes = cours.etudiants_concernes().count()
            cours.nb_inscrits_reel = cours.inscriptions.count()
        
        context = {
            'role': 'professeur',
            'cours_assignes': cours_assignes
        }
    
    elif user.role == User.Role.ETUDIANT:
        from grades.models import Note, InscriptionCours
        from academics.models import Cours

        if hasattr(user, 'etudiant'):
            notes_recentes = Note.objects.filter(
                etudiant=user.etudiant,
                statut='publiée'
            )[:5]

            cours_inscrits = Cours.objects.filter(
                inscriptions__etudiant=user.etudiant
            ).distinct()

            context = {
                'role': 'etudiant',
                'etudiant': user.etudiant,
                'notes_recentes': notes_recentes,
                'cours_inscrits': cours_inscrits
            }
        else:
            context = {'role': 'etudiant', 'etudiant': None}
    
    else:
        context = {'role': 'unknown'}
    
    return render(request, 'accounts/dashboard.html', context)


# ✅ CORRECTION : UTILISER LES PERMISSIONS GRANULAIRES
@login_required
@permission_required(is_admin)  # ✅ Au lieu de is_admin
def liste_etudiants(request):
    search = request.GET.get('search', '')
    etudiants_list = Etudiant.objects.select_related('user', 'faculte').order_by('faculte', 'niveau', 'user__last_name')
    if search:
        etudiants_list = etudiants_list.filter(
            user__last_name__icontains=search
        ) | etudiants_list.filter(matricule__icontains=search)
        if not etudiants_list.exists():
            messages.info(request, "Aucun étudiant ne correspond à votre recherche.")

    paginator = Paginator(etudiants_list, 10)
    page_number = request.GET.get('page')
    etudiants = paginator.get_page(page_number)
    return render(request, 'accounts/liste_etudiants.html', {'etudiants': etudiants})


@login_required
@user_passes_test(is_admin)
def rechercher_etudiants_ajax(request):
    search = request.GET.get('q', '')

    etudiants = Etudiant.objects.select_related('user', 'faculte').filter(
        Q(user__last_name__icontains=search) |
        Q(user__first_name__icontains=search) |
        Q(matricule__icontains=search) |
        Q(faculte__nom__icontains=search)
    ).order_by('user__last_name')[:20]

    data = []
    for e in etudiants:
        data.append({
            'id': e.id,
            'matricule': e.matricule,
            'nom': e.user.get_full_name(),
            'faculte': e.faculte.nom,
            'niveau': e.get_niveau_display(),
            'telephone': e.user.telephone or '—',
            'date': e.date_inscription.strftime('%d/%m/%Y')
        })

    return JsonResponse({'etudiants': data})



# ✅ CORRECTION : UTILISER LES PERMISSIONS GRANULAIRES  
@login_required
@permission_required(is_admin)  # ✅ Au lieu de is_admin
def liste_professeurs(request):
    search = request.GET.get('search', '')
    prof_list = Professeur.objects.select_related('user').order_by('user__last_name')
    if search:
        prof_list = prof_list.filter(user__last_name__icontains=search) | prof_list.filter(specialite__icontains=search)
        if not prof_list.exists():
            messages.info(request, "Aucun professeur ne correspond à votre recherche.")

    paginator = Paginator(prof_list, 10)
    page_number = request.GET.get('page')
    professeurs = paginator.get_page(page_number)
    return render(request, 'accounts/liste_professeurs.html', {'professeurs': professeurs})

 

@login_required
@user_passes_test(is_admin)
def rechercher_professeurs_ajax(request):
    search = request.GET.get('q', '')

    profs = Professeur.objects.select_related('user').filter(
        Q(user__last_name__icontains=search) |
        Q(user__first_name__icontains=search) |
        Q(specialite__icontains=search) |
        Q(statut__icontains=search)
    ).order_by('user__last_name')[:20]

    data = []
    for p in profs:
        data.append({
            'id': p.id,
            'nom': p.user.get_full_name(),
            'specialite': p.specialite,
            'statut': p.statut,
            'date': p.date_embauche.strftime('%d/%m/%Y'),
            'telephone': p.user.telephone or '—'
        })

    return JsonResponse({'professeurs': data})



# === VUES DE MODIFICATION ===

@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def modifier_etudiant(request, etudiant_id):
    """Modifier un étudiant existant"""
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    # Capturer l'ancien état pour l'audit
    ancienne_faculte = etudiant.faculte
    ancien_niveau = etudiant.niveau
    ancien_semestre = etudiant.semestre_courant

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=etudiant.user)  # ← Utiliser UserEditForm
        etu_form = EtudiantForm(request.POST, instance=etudiant)
        
        if user_form.is_valid() and etu_form.is_valid():
            # Capturer les changements avant sauvegarde
            changements = []
            
            if ancienne_faculte != etu_form.cleaned_data.get('faculte'):
                changements.append(f"Faculté: {ancienne_faculte} → {etu_form.cleaned_data.get('faculte')}")
            
            if ancien_niveau != etu_form.cleaned_data.get('niveau'):
                changements.append(f"Niveau: {ancien_niveau} → {etu_form.cleaned_data.get('niveau')}")
            
            if ancien_semestre != etu_form.cleaned_data.get('semestre_courant'):
                changements.append(f"Semestre: {ancien_semestre} → {etu_form.cleaned_data.get('semestre_courant')}")

            user_form.save()
            etu_form.save()
            # ✅ AUDIT: Modification
            if changements:
                audit_modifier_etudiant(request, etudiant, ", ".join(changements))
            else:
                audit_modifier_etudiant(request, etudiant, "Informations personnelles modifiées")

            messages.success(request, "Étudiant modifié avec succès")
            return redirect('accounts:liste_etudiants')
    else:
        user_form = UserEditForm(instance=etudiant.user)  # ← Utiliser UserEditForm
        etu_form = EtudiantForm(instance=etudiant)
    
    return render(request, 'accounts/modifier_etudiant.html', {
        'user_form': user_form,
        'etu_form': etu_form,
        'etudiant': etudiant
    })


@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def modifier_professeur(request, professeur_id):
    """Modifier un professeur existant"""
    professeur = get_object_or_404(Professeur, id=professeur_id)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=professeur.user)
        prof_form = ProfesseurForm(request.POST, instance=professeur)
        
        if user_form.is_valid() and prof_form.is_valid():
            user_form.save()
            prof_form.save()
            messages.success(request, "Professeur modifié avec succès")
            return redirect('accounts:liste_professeurs')
    else:
        user_form = UserForm(instance=professeur.user)
        prof_form = ProfesseurForm(instance=professeur)
    
    return render(request, 'accounts/modifier_professeur.html', {
        'user_form': user_form,
        'prof_form': prof_form,
        'professeur': professeur
    })

@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def supprimer_etudiant(request, etudiant_id):
    """Supprimer un étudiant"""
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    
    if request.method == 'POST':
        # ✅ AUDIT: Suppression (AVANT la suppression pour garder les infos)
        audit_supprimer_etudiant(request, etudiant)
        user = etudiant.user
        etudiant.delete()
        user.delete()
        messages.success(request, "Étudiant supprimé avec succès")
        return redirect('accounts:liste_etudiants')
    
    return render(request, 'accounts/supprimer_etudiant.html', {
        'etudiant': etudiant
    })

@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def supprimer_professeur(request, professeur_id):
    """Supprimer un professeur"""
    professeur = get_object_or_404(Professeur, id=professeur_id)
    
    if request.method == 'POST':
         # ✅ AUDIT: Suppression
        audit_supprimer_professeur(request, professeur)

        user = professeur.user
        professeur.delete()
        user.delete()
        messages.success(request, "Professeur supprimé avec succès")
        return redirect('accounts:liste_professeurs')
    
    return render(request, 'accounts/supprimer_professeur.html', {
        'professeur': professeur
    })




 
@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def export_professeurs_csv(request):
    search = request.GET.get('q', '').strip()
    # ✅ AUDIT: Export avant génération
    audit_action_generique(request, 'EXPORT_DATA', 
                          'Export professeurs CSV', 
                          f"Export des professeurs. Filtre: '{search}'")

    profs = Professeur.objects.select_related('user')

    if search:
        profs = profs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(specialite__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="professeurs.csv"'

    output = io.TextIOWrapper(response, encoding='utf-8-sig', newline='')
    writer = csv.writer(output)

    # Entête
    writer.writerow(['NOM', 'PRENOM', 'SPECIALITE', 'STATUT', 'TELEPHONE'])

    # Données
    for p in profs:
        writer.writerow([
            p.user.last_name,
            p.user.first_name,
            p.specialite,
            p.statut,
            p.user.telephone or ''
        ])

    output.flush()
    return response


@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def export_etudiants_csv(request):
    search = request.GET.get('q', '').strip()
    # ✅ AUDIT: Export avant génération
    audit_action_generique(request, 'EXPORT_DATA', 
                          'Export étudiants CSV', 
                          f"Export des étudiants. Filtre: '{search}'")

    etudiants = Etudiant.objects.select_related('user', 'faculte')

    if search:
        etudiants = etudiants.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(matricule__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="etudiants.csv"'

    output = io.TextIOWrapper(response, encoding='utf-8-sig', newline='')
    writer = csv.writer(output)

    # Entête
    writer.writerow(['MATRICULE', 'NOM', 'PRENOM', 'FACULTE', 'NIVEAU'])

    # Données
    for e in etudiants:
        writer.writerow([
            e.matricule,
            e.user.last_name,
            e.user.first_name,
            e.faculte.nom,
            e.get_niveau_display()
        ])

    output.flush()
    return response




# Décorateur pour vérifier si l'utilisateur est admin
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            messages.error(request, "❌ Accès réservé aux administrateurs")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

# accounts/views.py
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
#@admin_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def gestion_utilisateurs(request):
    """
    Admin: Liste et gestion de tous les utilisateurs avec pagination
    """
    # Paramètres de filtrage
    role = request.GET.get('role', '')
    statut = request.GET.get('statut', '')
    search = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Base queryset
    utilisateurs = User.objects.all().order_by('-date_joined')
    
    # Appliquer les filtres
    if role:
        utilisateurs = utilisateurs.filter(role=role)
    
    if statut == 'actif':
        utilisateurs = utilisateurs.filter(is_active=True)
    elif statut == 'inactif':
        utilisateurs = utilisateurs.filter(is_active=False)
    
    if search:
        utilisateurs = utilisateurs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Pagination (10 utilisateurs par page)
    paginator = Paginator(utilisateurs, 8)
    
    try:
        utilisateurs_page = paginator.page(page)
    except PageNotAnInteger:
        utilisateurs_page = paginator.page(1)
    except EmptyPage:
        utilisateurs_page = paginator.page(paginator.num_pages)
    
    # Si c'est une requête AJAX, retourner seulement le tableau
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        context = {
            'utilisateurs': utilisateurs_page,
            'page_obj': utilisateurs_page,
        }
        return render(request, 'accounts/_users_table_rows.html', context)
    
    # Pour requête normale
    context = {
        'page_obj': utilisateurs_page,
        'utilisateurs': utilisateurs_page,  # Pour compatibilité
        'roles': User.Role.choices,
        'selected_role': role,
        'selected_statut': statut,
        'search_query': search,
        'total_users': paginator.count,
    }
    
    return render(request, 'accounts/gestion_utilisateurs.html', context)


# @login_required
# @admin_required
# def gestion_utilisateurs(request):
#     """
#     Admin: Liste et gestion de tous les utilisateurs
#     """
#     # Paramètres de filtrage
#     role = request.GET.get('role', '')
#     statut = request.GET.get('statut', '')
#     search = request.GET.get('search', '')
    
#     # Base queryset
#     utilisateurs = User.objects.all()
    
#     # Appliquer les filtres
#     if role:
#         utilisateurs = utilisateurs.filter(role=role)
    
#     if statut == 'actif':
#         utilisateurs = utilisateurs.filter(is_active=True)
#     elif statut == 'inactif':
#         utilisateurs = utilisateurs.filter(is_active=False)
    
#     if search:
#         utilisateurs = utilisateurs.filter(
#             Q(username__icontains=search) |
#             Q(email__icontains=search) |
#             Q(first_name__icontains=search) |
#             Q(last_name__icontains=search)
#         )
    
#     # Trier par date d'inscription (plus récent d'abord)
#     utilisateurs = utilisateurs.order_by('-date_joined')
    
#     context = {
#         'utilisateurs': utilisateurs,
#         'roles': User.Role.choices,
#         'selected_role': role,
#         'selected_statut': statut,
#         'search_query': search,
#     }
    
#     return render(request, 'accounts/gestion_utilisateurs.html', context)

@login_required
@admin_required
def detail_utilisateur(request, user_id):
    """
    Admin: Détail d'un utilisateur avec actions
    """
    utilisateur = get_object_or_404(User, id=user_id)
    
    # Récupérer les informations spécifiques selon le rôle
    infos_supplementaires = None
    if utilisateur.role == User.Role.ETUDIANT:
        try:
            infos_supplementaires = Etudiant.objects.get(user=utilisateur)
        except Etudiant.DoesNotExist:
            pass
    elif utilisateur.role == User.Role.PROFESSEUR:
        try:
            infos_supplementaires = Professeur.objects.get(user=utilisateur)
        except Professeur.DoesNotExist:
            pass
    
    context = {
        'utilisateur': utilisateur,
        'infos_supplementaires': infos_supplementaires,
    }
    
    return render(request, 'accounts/detail_utilisateur.html', context)

@login_required
#@admin_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def toggle_activation(request, user_id):
    """
    Admin: Activer/désactiver un compte utilisateur
    """
    utilisateur = get_object_or_404(User, id=user_id)
    
    # Empêcher de désactiver son propre compte
    if utilisateur == request.user:
        messages.error(request, "❌ Vous ne pouvez pas désactiver votre propre compte")
        return redirect('accounts:detail_utilisateur', user_id=user_id)
    
    # Toggle l'état actif/inactif
    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save()
    
    if utilisateur.is_active:
        messages.success(request, f"✅ Compte de {utilisateur.get_full_name()} activé avec succès")
    else:
        messages.warning(request, f"⚠️ Compte de {utilisateur.get_full_name()} désactivé avec succès")
    
    return redirect('accounts:detail_utilisateur', user_id=user_id)


@login_required
@permission_required(can_manage_users, redirect_url='accounts:dashboard')
def changer_role(request, user_id):
    """
    Admin: Changer le rôle d'un utilisateur
    """
    utilisateur = get_object_or_404(User, id=user_id)
    
    # Empêcher de modifier son propre rôle
    if utilisateur == request.user:
        messages.error(request, "❌ Vous ne pouvez pas modifier votre propre rôle")
        return redirect('accounts:detail_utilisateur', user_id=user_id)
    
    if request.method == 'POST':
        nouveau_role = request.POST.get('role')
        
        if nouveau_role in [role[0] for role in User.Role.choices]:
            ancien_role = utilisateur.get_role_display()
            utilisateur.role = nouveau_role
            utilisateur.save()
            
            messages.success(request, 
                f"✅ Rôle de {utilisateur.get_full_name()} changé: {ancien_role} → {utilisateur.get_role_display()}"
            )
    
    return redirect('accounts:detail_utilisateur', user_id=user_id)


@login_required
def mon_profil(request):
    """Affiche et permet de modifier les informations personnelles de l'utilisateur"""
    user = request.user
    
    # Récupérer les informations supplémentaires selon le rôle
    info_supplementaires = {}
    full_info = {}
    
    if user.role == 'student':
        try:
            etudiant = Etudiant.objects.get(user=user)
            info_supplementaires = {
                'matricule': etudiant.matricule,
                'faculte': etudiant.faculte,
                'niveau': etudiant.get_niveau_display(),
                'date_inscription': etudiant.date_inscription,
                'adresse': etudiant.adresse,
                'date_naissance': etudiant.date_naissance,
                'sexe': etudiant.get_sexe_display(),
                'telephone_parent': etudiant.telephone_parent,
            }
            full_info = {   
                'semestre_courant': etudiant.get_semestre_courant_display(),
                'date_inscription': etudiant.date_inscription.strftime('%d/%m/%Y'),
                'adresse': etudiant.adresse,
                'date_naissance': etudiant.date_naissance.strftime('%d/%m/%Y'),
                'sexe': etudiant.get_sexe_display(),
                'telephone_parent': etudiant.telephone_parent or 'Non renseigné',
            }
        except ObjectDoesNotExist:
            pass
    
    elif user.role == 'prof':
        try:
            professeur = Professeur.objects.get(user=user)
            info_supplementaires = {
                'specialite': professeur.specialite,
                'date_embauche': professeur.date_embauche,
                'statut': professeur.get_statut_display(),
            }
        except ObjectDoesNotExist:
            pass
    
    elif user.role == 'admin':
        try:
            admin = Admin.objects.get(user=user)
            info_supplementaires = {
                'date_nomination': admin.date_nomination,
                'niveau_acces': admin.get_niveau_acces_display(),
            }
        except ObjectDoesNotExist:
            pass
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vos informations ont été mises à jour avec succès.')
            return redirect('accounts:mon_profil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = UserProfileForm(instance=user)
    
    context = {
        'user': user,
        'form': form,
        'info_supp': info_supplementaires,
    }
    
    return render(request, 'accounts/mon_profil.html', context)


# accounts/views.py

@login_required
@user_passes_test(is_admin)
def voir_profil_utilisateur(request, user_id):
    utilisateur = get_object_or_404(User, id=user_id)

    info_supp = {}

    if utilisateur.role == 'student':
        try:
            etudiant = Etudiant.objects.get(user=utilisateur)
            info_supp = {
                'matricule': etudiant.matricule,
                'faculte': etudiant.faculte,
                'niveau': etudiant.get_niveau_display(),
                'semestre': etudiant.get_semestre_courant_display(),
                'date_naissance': etudiant.date_naissance,
                'sexe': etudiant.get_sexe_display(),
                'adresse': etudiant.adresse,
                'telephone_parent': etudiant.telephone_parent,
                'date_inscription': etudiant.date_inscription,
            }
        except ObjectDoesNotExist:
            pass

    elif utilisateur.role == 'prof':
        try:
            professeur = Professeur.objects.get(user=utilisateur)
            info_supp = {
                'specialite': professeur.specialite,
                #'grade': professeur.get_grade_display(),
                'statut': professeur.get_statut_display(),
                'date_embauche': professeur.date_embauche,
            }
        except ObjectDoesNotExist:
            pass

    elif utilisateur.role == 'admin':
        try:
            admin = Admin.objects.get(user=utilisateur)
            info_supp = {
                'niveau_acces': admin.get_niveau_acces_display(),
                'date_nomination': admin.date_nomination,
            }
        except ObjectDoesNotExist:
            pass

    context = {
        'utilisateur': utilisateur,
        'info_supp': info_supp,
    }

    return render(request, 'accounts/profil_utilisateur_admin.html', context)



#Pour auditer
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import now, timedelta
from datetime import datetime
from .models import AuditAction

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import now, timedelta, make_aware
from datetime import datetime, date
from django.shortcuts import render
from .models import AuditAction

@user_passes_test(is_admin)
def vue_audit(request):
    """Vue pour consulter les actions d'audit avec filtres CORRIGÉE"""
    
    # Récupérer tous les types d'actions disponibles pour le filtre
    actions_choices = AuditAction.ACTIONS
    
    # Initialisation des filtres
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    objet_filter = request.GET.get('objet', '')
    faculte_filter = request.GET.get('faculte', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    periode = request.GET.get('periode', '')
    
    # Filtrer les actions d'audit
    audits = AuditAction.objects.all()
    
    # Filtre par utilisateur
    if user_filter:
        audits = audits.filter(user__icontains=user_filter)
    
    # Filtre par action
    if action_filter:
        audits = audits.filter(action=action_filter)
    
    # Filtre par objet
    if objet_filter:
        audits = audits.filter(objet__icontains=objet_filter)
    
    # Filtre par faculté
    if faculte_filter:
        audits = audits.filter(faculte__icontains=faculte_filter)
    
    # CORRECTION : Gestion correcte des périodes avec timezone
    today_local = now().date()  # Date locale
    
    # Filtre par période prédéfinie
    if periode:
        if periode == 'today':
            # Filtrer pour aujourd'hui (toute la journée en UTC)
            start_of_day = make_aware(datetime.combine(today_local, datetime.min.time()))
            end_of_day = make_aware(datetime.combine(today_local, datetime.max.time()))
            audits = audits.filter(date__range=[start_of_day, end_of_day])
            
        elif periode == 'yesterday':
            yesterday = today_local - timedelta(days=1)
            start_of_day = make_aware(datetime.combine(yesterday, datetime.min.time()))
            end_of_day = make_aware(datetime.combine(yesterday, datetime.max.time()))
            audits = audits.filter(date__range=[start_of_day, end_of_day])
            
        elif periode == 'week':
            week_ago = today_local - timedelta(days=7)
            start_of_day = make_aware(datetime.combine(week_ago, datetime.min.time()))
            end_of_day = make_aware(datetime.combine(today_local, datetime.max.time()))
            audits = audits.filter(date__range=[start_of_day, end_of_day])
            
        elif periode == 'month':
            month_ago = today_local - timedelta(days=30)
            start_of_day = make_aware(datetime.combine(month_ago, datetime.min.time()))
            end_of_day = make_aware(datetime.combine(today_local, datetime.max.time()))
            audits = audits.filter(date__range=[start_of_day, end_of_day])
    
    # CORRECTION : Filtre par date personnalisée avec timezone
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            start_of_day = make_aware(datetime.combine(date_debut_obj, datetime.min.time()))
            audits = audits.filter(date__gte=start_of_day)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            end_of_day = make_aware(datetime.combine(date_fin_obj, datetime.max.time()))
            audits = audits.filter(date__lte=end_of_day)
        except ValueError:
            pass
    
    # Trier par date décroissante
    audits = audits.order_by('-date')
    
    # Pagination
    paginator = Paginator(audits, 50)  # 50 éléments par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # CORRECTION : Statistiques avec timezone
    start_of_today = make_aware(datetime.combine(today_local, datetime.min.time()))
    end_of_today = make_aware(datetime.combine(today_local, datetime.max.time()))
    
    total_actions = audits.count()
    actions_today = AuditAction.objects.filter(
        date__range=[start_of_today, end_of_today]
    ).count()
    
    # Récupérer les utilisateurs uniques pour le filtre
    users_list = AuditAction.objects.values_list('user', flat=True).distinct().order_by('user')
    
    # Récupérer les facultés uniques pour le filtre
    facultes_list = AuditAction.objects.exclude(faculte='').values_list('faculte', flat=True).distinct().order_by('faculte')
    
    # CORRECTION : Définir la date du jour pour les champs date
    today_str = today_local.strftime('%Y-%m-%d')
    
    context = {
        'page_obj': page_obj,
        'total_actions': total_actions,
        'actions_today': actions_today,
        'actions_choices': actions_choices,
        'users_list': users_list,
        'facultes_list': facultes_list,
        'filters': {
            'user': user_filter,
            'action': action_filter,
            'objet': objet_filter,
            'faculte': faculte_filter,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'periode': periode,
        },
        'today': today_str,  # Pour la valeur par défaut des champs date
    }
    
    return render(request, 'accounts/audit.html', context)


# def vue_audit(request):
#     """Vue pour consulter les actions d'audit avec filtres"""
    
#     # Récupérer tous les types d'actions disponibles pour le filtre
#     actions_choices = AuditAction.ACTIONS
    
#     # Initialisation des filtres
#     user_filter = request.GET.get('user', '')
#     action_filter = request.GET.get('action', '')
#     objet_filter = request.GET.get('objet', '')
#     faculte_filter = request.GET.get('faculte', '')
#     date_debut = request.GET.get('date_debut', '')
#     date_fin = request.GET.get('date_fin', '')
#     periode = request.GET.get('periode', '')
    
#     # Filtrer les actions d'audit
#     audits = AuditAction.objects.all()
    
#     # Filtre par utilisateur
#     if user_filter:
#         audits = audits.filter(user__icontains=user_filter)
    
#     # Filtre par action
#     if action_filter:
#         audits = audits.filter(action=action_filter)
    
#     # Filtre par objet
#     if objet_filter:
#         audits = audits.filter(objet__icontains=objet_filter)
    
#     # Filtre par faculté
#     if faculte_filter:
#         audits = audits.filter(faculte__icontains=faculte_filter)
    
#     # Filtre par période prédéfinie
#     if periode:
#         today = now().date()
#         if periode == 'today':
#             audits = audits.filter(date__date=today)
#         elif periode == 'yesterday':
#             yesterday = today - timedelta(days=1)
#             audits = audits.filter(date__date=yesterday)
#         elif periode == 'week':
#             week_ago = today - timedelta(days=7)
#             audits = audits.filter(date__date__gte=week_ago)
#         elif periode == 'month':
#             month_ago = today - timedelta(days=30)
#             audits = audits.filter(date__date__gte=month_ago)
    
#     # Filtre par date personnalisée
#     if date_debut:
#         try:
#             date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
#             audits = audits.filter(date__date__gte=date_debut_obj)
#         except ValueError:
#             pass
    
#     if date_fin:
#         try:
#             date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
#             audits = audits.filter(date__date__lte=date_fin_obj)
#         except ValueError:
#             pass
    
#     # Trier par date décroissante
#     audits = audits.order_by('-date')
    
#     # Pagination
#     paginator = Paginator(audits, 50)  # 50 éléments par page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     # Statistiques
#     total_actions = audits.count()
#     actions_today = AuditAction.objects.filter(date__date=now().date()).count()
    
#     # Récupérer les utilisateurs uniques pour le filtre
#     users_list = AuditAction.objects.values_list('user', flat=True).distinct().order_by('user')
    
#     # Récupérer les facultés uniques pour le filtre
#     facultes_list = AuditAction.objects.exclude(faculte='').values_list('faculte', flat=True).distinct().order_by('faculte')
    
#     context = {
#         'page_obj': page_obj,
#         'total_actions': total_actions,
#         'actions_today': actions_today,
#         'actions_choices': actions_choices,
#         'users_list': users_list,
#         'facultes_list': facultes_list,
#         'filters': {
#             'user': user_filter,
#             'action': action_filter,
#             'objet': objet_filter,
#             'faculte': faculte_filter,
#             'date_debut': date_debut,
#             'date_fin': date_fin,
#             'periode': periode,
#         }
#     }
    
#     return render(request, 'accounts/audit.html', context)

