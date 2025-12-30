from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse

from accounts.views import (
    can_manage_academique, can_manage_cours, can_manage_facultes, 
    can_validate_grades, can_manage_users, is_admin, 
    can_manage_annonces, can_access_academique, permission_required  # ✅ AJOUTER
)
from .models import Cours, Faculte  # ✅ SUPPRIMER Inscription
from accounts.models import Admin, User
from .forms import CoursForm, FaculteForm 
from django.core.paginator import Paginator    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone 
from .models import Annonce
from .forms import AnnonceForm
from django.db.models import Q
User = get_user_model()  
from django.http import HttpResponse 
import csv
import io 

 
from django.template.loader import render_to_string  

 
# AJOUTEZ CET IMPORT EN HAUT DU FICHIER
from accounts.audit_utils import (
    audit_creer_cours, audit_modifier_cours, audit_supprimer_cours,
    audit_creer_faculte, audit_supprimer_faculte,
    audit_creer_annonce, audit_supprimer_annonce,
    audit_action_generique
)

 
 

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def creer_cours(request):
    if request.method == 'POST':
        form = CoursForm(request.POST)
        if form.is_valid():
            cours=form.save()
            # ✅ AUDIT SIMPLE MAIS COMPLET
            audit_creer_cours(request, cours)
            messages.success(request, "✅ Cours créé avec succès.")
            return redirect('academics:liste_cours')
        else:
            # 🔴 Formulaire invalide
            messages.error(
                request,
                "❌ Le formulaire contient des erreurs. Veuillez corriger les champs en rouge."
            )
    else:
        form = CoursForm()

    return render(request, 'academics/creer_cours.html', {'form': form})




@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def gestion_cours(request):
    cours_list = Cours.objects.all().order_by('faculte', 'niveau')

    paginator = Paginator(cours_list, 10)
    page_number = request.GET.get('page')
    cours = paginator.get_page(page_number)

    return render(
        request,
        'academics/gestion_cours.html',
        {'cours': cours}
    )

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def recherche_cours_ajax(request):
    q = request.GET.get('q', '').strip()

    cours = Cours.objects.select_related(
        'faculte', 'professeur'
    ).filter(
        Q(code__icontains=q) |
        Q(intitule__icontains=q) |
        Q(faculte__nom__icontains=q) |
        Q(professeur__first_name__icontains=q) |
        Q(professeur__last_name__icontains=q)
    ).order_by('intitule')[:20]

    data = []
    for c in cours:
        data.append({
            'id': c.id,
            'code': c.code,
            'intitule': c.intitule,
            'faculte': c.faculte.nom,
            'niveau': c.get_niveau_display(),
            'semestre': c.get_semestre_display(),
            'credits': c.credits,
            'professeur': c.professeur.get_full_name() if c.professeur else 'Non assigné'
        })

    return JsonResponse({'cours': data})


@login_required
def mes_cours_professeur(request):
    """Professeur: Voir ses cours assignés"""
    if request.user.role != User.Role.PROFESSEUR:
        messages.error(request, "Accès réservé aux professeurs")
        return redirect('accounts:dashboard')
    
    cours_assignes = Cours.objects.filter(professeur=request.user)
    
    context = {
        'cours_assignes': cours_assignes,
    }
    return render(request, 'academics/mes_cours_professeur.html', context)

@login_required
def mes_cours_etudiant(request):
    """Étudiant: Voir les cours de sa faculté/niveau"""
    if request.user.role != User.Role.ETUDIANT or not hasattr(request.user, 'etudiant'):
        messages.error(request, "Accès réservé aux étudiants")
        return redirect('accounts:dashboard')
    
    etudiant = request.user.etudiant
    mes_cours = Cours.objects.filter(
        inscriptions__etudiant=etudiant
    ).distinct().select_related('professeur', 'faculte')
    
    context = {
        'etudiant': etudiant,
        'mes_cours': mes_cours,
    }
    return render(request, 'academics/mes_cours_etudiant.html', context)

@login_required
@permission_required(is_admin, redirect_url='accounts:dashboard')
def liste_facultes(request):
    """Liste des facultés"""
    facultes = Faculte.objects.all()
    return render(request, 'academics/liste_facultes.html', {'facultes': facultes})

from django.core.paginator import Paginator
 


@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def liste_cours(request):
    """
    Liste des cours selon le rôle de l'utilisateur
    - Admin : tous les cours
    - Professeur : ses cours uniquement
    """

    user = request.user

    if user.role == User.Role.PROFESSEUR:
        cours_qs = Cours.objects.filter(professeur=user)
    else:
        # Admin ou autre rôle autorisé
        cours_qs = Cours.objects.select_related(
            'faculte', 'professeur'
        ).all()

    cours_qs = cours_qs.order_by('faculte__nom', 'niveau', 'intitule')

    # Pagination
    paginator = Paginator(cours_qs, 10)  # 10 cours par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'cours_list': page_obj,     # 🔑 NOM ATTENDU PAR LE TEMPLATE
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }

    return render(request, 'academics/liste_cours.html', context)




def cours_par_faculte_modal(request):
    """Retourne les cours HTML d'une faculté pour le modal"""
    faculte_id = request.GET.get('faculte_id')
    faculte = Faculte.objects.filter(id=faculte_id).first()
    cours = Cours.objects.filter(faculte=faculte) if faculte else []
    
    html = render_to_string('academics/partials/cours_modal_content.html', {
        'cours': cours
    })
    return JsonResponse({'html': html})

  

def annonce_detail_modal(request):
    """Retourne le détail complet d'une annonce pour le modal"""
    annonce_id = request.GET.get('annonce_id')
    annonce = Annonce.objects.filter(id=annonce_id).first()

    html = render_to_string('academics/partials/annonce_modal_content.html', {
        'annonce': annonce
    })
    return JsonResponse({'html': html})



@login_required
@user_passes_test(lambda u: u.is_staff)
def rechercher_cours_ajax(request):
    search = request.GET.get('q', '').strip()

    cours = Cours.objects.select_related(
        'faculte', 'professeur'
    ).filter(
        Q(code__icontains=search) |
        Q(intitule__icontains=search) |
        Q(faculte__nom__icontains=search) |
        Q(professeur__last_name__icontains=search) |
        Q(professeur__first_name__icontains=search)
    ).order_by('intitule')[:20]

    data = []
    for c in cours:
        data.append({
            'id': c.id,
            'code': c.code,
            'intitule': c.intitule,
            'faculte': c.faculte.nom,
            'niveau': c.get_niveau_display(),
            'semestre': c.get_semestre_display(),
            'credits': c.credits,
            'professeur': c.professeur.get_full_name() if c.professeur else 'Non assigné'
        })

    return JsonResponse({'cours': data})


# @login_required
# def rechercher_cours_ajax(request):
#     search = request.GET.get('q', '').strip()

#     # 🔐 Respect du rôle
#     if request.user.role == 'professeur':
#         cours_qs = Cours.objects.filter(professeur=request.user)
#     else:
#         cours_qs = Cours.objects.all()

#     cours_qs = cours_qs.select_related(
#         'faculte', 'professeur__user'
#     ).filter(
#         Q(intitule__icontains=search) |
#         Q(code__icontains=search) |
#         Q(faculte__nom__icontains=search) |
#         Q(professeur__user__last_name__icontains=search) |
#         Q(professeur__user__first_name__icontains=search)
#     ).order_by('intitule')[:20]

#     data = []
#     for c in cours_qs:
#         data.append({
#             'id': c.id,
#             'intitule': c.intitule,
#             'code': c.code or '',
#             'faculte': c.faculte.nom,
#             'professeur': (
#                 c.professeur.user.get_full_name()
#                 if c.professeur else 'Non assigné'
#             ),
#             'niveau': c.get_niveau_display(),
#             'semestre': c.get_semestre_display(),
#             'credits': c.credits
#         })

#     return JsonResponse({'cours': data})

 


@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def modifier_cours(request, cours_id):
    """Modifier un cours existant"""
    cours = get_object_or_404(Cours, id=cours_id)
    # Capturer l'ancien état si nécessaire
    ancien_professeur = cours.professeur
    ancien_intitule = cours.intitule
    
    if request.method == 'POST':
        form = CoursForm(request.POST, instance=cours)
        if form.is_valid():
            form.save()
            cours = form.save()
            
            # ✅ AUDIT avec détails des changements
            changements = []
            if ancien_professeur != cours.professeur:
                changements.append(f"Professeur: {ancien_professeur} → {cours.professeur}")
            if ancien_intitule != cours.intitule:
                changements.append(f"Intitulé modifié")
            
            details_changements = ", ".join(changements) if changements else "Informations générales modifiées"
            audit_modifier_cours(request, cours, details_changements)

            messages.success(request, "Cours modifié avec succès")
            return redirect('academics:liste_cours')
    else:
        form = CoursForm(instance=cours)
    
    return render(request, 'academics/modifier_cours.html', {
        'form': form,
        'cours': cours
    })

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def supprimer_cours(request, cours_id):
    """Supprimer un cours"""
    cours = get_object_or_404(Cours, id=cours_id)
    
    if request.method == 'POST':
        # ✅ AUDIT AVANT la suppression (pour garder les infos)
        audit_supprimer_cours(request, cours)

        cours.delete()
        messages.success(request, "Cours supprimé avec succès")
        return redirect('academics:liste_cours')
    
    return render(request, 'academics/supprimer_cours.html', {
        'cours': cours
    })


# ... vos vues existantes ...

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def creer_faculte(request):
    if request.method == 'POST':
        form = FaculteForm(request.POST)
        if form.is_valid():
            #form.save()
            faculte = form.save()
            
            # ✅ AUDIT
            audit_creer_faculte(request, faculte)

            messages.success(request, "Faculté créée avec succès")
            return redirect('academics:liste_facultes')
    else:
        form = FaculteForm()

    return render(request, 'academics/creer_faculte.html', {'form': form})


@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def modifier_faculte(request, faculte_id):
    faculte = get_object_or_404(Faculte, id=faculte_id)

    if request.method == 'POST':
        form = FaculteForm(request.POST, instance=faculte)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculté modifiée avec succès")
            return redirect('academics:liste_facultes')
    else:
        form = FaculteForm(instance=faculte)

    return render(request, 'academics/modifier_faculte.html', {
        'form': form,
        'faculte': faculte
    })



@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def supprimer_faculte(request, faculte_id):
    faculte = get_object_or_404(Faculte, id=faculte_id)

    if request.method == 'POST':
        # ✅ AUDIT AVANT suppression
        audit_supprimer_faculte(request, faculte)
        faculte.delete()
        messages.success(request, "Faculté supprimée avec succès")
        return redirect('academics:liste_facultes')

    return render(request, 'academics/supprimer_faculte.html', {
        'faculte': faculte
    })


# @login_required
# @user_passes_test(can_manage_facultes)
# def liste_facultes(request):
#     facultes = Faculte.objects.all().order_by('nom')
#     return render(request, 'academics/liste_facultes.html', {
#         'facultes': facultes
#     })



 
@login_required
#@user_passes_test(can_manage_users)
def export_cours_csv(request):
    # Récupérer le filtre de recherche si présent
    q = request.GET.get('q', '').strip()
     # ✅ AUDIT: Export
    audit_action_generique(request, 'EXPORT_DATA', 
                          'Export cours CSV', 
                          f"Export des cours. Filtre: '{q}'")

    # Sélection de base
    qs = Cours.objects.select_related('faculte', 'professeur').all()

    # 🔐 Respect du rôle : si c'est un professeur, il ne voit que ses cours
    if request.user.role == 'professeur':
        qs = qs.filter(professeur=request.user)

    # Application du filtre de recherche
    if q:
        qs = qs.filter(
            Q(code__icontains=q) |
            Q(intitule__icontains=q) |
            Q(faculte__nom__icontains=q) |
            Q(professeur__last_name__icontains=q) |
            Q(professeur__first_name__icontains=q)
        )

    # Création de la réponse HTTP
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cours.csv"'

    # ⚡ Gestion correcte de l'encodage
    output = io.TextIOWrapper(response, encoding='utf-8-sig', newline='')
    writer = csv.writer(output)

    # Écriture de l'entête
    writer.writerow(['Code', 'Intitulé', 'Faculté', 'Niveau', 'Semestre', 'Crédits', 'Professeur'])

    # Écriture des données
    for c in qs:
        writer.writerow([
            c.code,
            c.intitule,
            c.faculte.nom,
            c.get_niveau_display(),
            c.get_semestre_display(),
            c.credits,
            c.professeur.get_full_name() if c.professeur else 'Non assigné'
        ])

    output.flush()  # ⚡ Assure que tout est écrit dans la réponse

    return response



# views pour gerer les annonces


# Décorateur pour vérifier les permissions
def can_manage_annonces(user):
    """Vérifie si l'utilisateur peut gérer les annonces"""
    if not user.is_authenticated:
        return False
    
    # Vérifie si c'est un admin via le rôle
    if user.role == User.Role.ADMIN:
        return True
    
    # Vérifie si l'utilisateur a un profil Admin
    try:
        admin_profile = user.admin
        # Vous pouvez ajouter des vérifications spécifiques ici
        # Exemple: vérifier une permission spécifique
        return True
    except Admin.DoesNotExist:
        return False

@login_required
#@user_passes_test(can_manage_annonces)
def liste_annonces(request):
    """Liste toutes les annonces avec filtres"""
    now = timezone.now()
    
    # Récupérer tous les paramètres
    type_filter = request.GET.get('type')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    # Initialiser le queryset de base
    annonces = Annonce.objects.all().order_by('-date_publication')
    
    # Appliquer les filtres (pour requêtes normales ET AJAX)
    if type_filter:
        annonces = annonces.filter(type_annonce=type_filter)
    
    # CRITIQUE : Correction du filtre "expired"
    # Une annonce est expirée si sa date d'expiration est passée
    # Cela peut concerner des annonces publiées ou non
    if status_filter == 'active':
        annonces = annonces.filter(est_publie=True, date_expiration__gt=now)
    elif status_filter == 'expired':
        # Filtrer uniquement les annonces dont la date d'expiration est passée
        annonces = annonces.filter(date_expiration__lt=now)
    elif status_filter == 'draft':
        annonces = annonces.filter(est_publie=False)
    
    # APPLIQUER LA RECHERCHE
    if search_query:
        annonces = annonces.filter(
            Q(titre__icontains=search_query) |
            Q(contenu__icontains=search_query) |
            Q(type_annonce__icontains=search_query) |
            Q(faculte__nom__icontains=search_query) |
            Q(auteur__first_name__icontains=search_query) |
            Q(auteur__last_name__icontains=search_query) |
            Q(auteur__username__icontains=search_query)
        ).distinct()
    
    # CALCULER LES STATISTIQUES RÉELLES
    # Total général
    total_annonces = annonces.count()
    
    # Annonces actives (publiées ET non expirées)
    active_annonces = annonces.filter(
        est_publie=True,
        date_expiration__gt=now
    ).count()
    
    # Annonces expirées (date expiration passée)
    expired_annonces = annonces.filter(
        date_expiration__lt=now
    ).count()
    
    # Annonces sans date d'expiration
    no_expiration_annonces = annonces.filter(
        date_expiration__isnull=True
    ).count()
    
    # Annonces urgentes (priorité 'critique' ou type 'urgence')
    urgent_annonces = annonces.filter(
        Q(priorite='critique') | Q(type_annonce='urgence')
    ).count()
    
    # Annonces brouillons
    draft_annonces = annonces.filter(est_publie=False).count()
    
    # Annonces importantes
    important_annonces = annonces.filter(est_important=True).count()
    
    # Ajouter une annotation pour le statut d'expiration dans le queryset
    # Cela permet d'afficher le statut directement dans le template
    from django.db.models import Case, When, Value, BooleanField
    annonces = annonces.annotate(
        is_expired=Case(
            When(date_expiration__lt=now, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        ),
        is_active=Case(
            When(est_publie=True, date_expiration__gt=now, then=Value(True)),
            When(est_publie=True, date_expiration__isnull=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    )
    
    # Pagination (uniquement pour requêtes normales)
    paginator = Paginator(annonces, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Si requête AJAX, retourner JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        annonces_data = []
        for annonce in annonces[:50]:
            # Déterminer si l'annonce est expirée
            est_expiree = annonce.date_expiration and annonce.date_expiration < now
            
            annonces_data.append({
                'id': annonce.id,
                'titre': annonce.titre,
                'type': annonce.get_type_annonce_display(),
                'type_code': annonce.type_annonce,
                'date_publication': annonce.date_publication.strftime('%d/%m/%Y %H:%M'),
                'date_expiration': annonce.date_expiration.strftime('%d/%m/%Y %H:%M') if annonce.date_expiration else 'Pas de date',
                'est_publie': annonce.est_publie,
                'est_active': annonce.est_publie and (not annonce.date_expiration or annonce.date_expiration > now),
                'est_expiree': est_expiree,  # Nouveau champ pour statut expiration
                'est_important': annonce.est_important,
                'faculte': annonce.faculte.nom if annonce.faculte else 'Toutes',
                'auteur': annonce.auteur.get_full_name() if annonce.auteur else 'Inconnu',
                'edit_url': reverse('academics:editer_annonce', args=[annonce.pk]),
            })
        
        return JsonResponse({
            'success': True,
            'annonces': annonces_data,
            'total': total_annonces,
            'search_query': search_query,
            'stats': {
                'active': active_annonces,
                'expired': expired_annonces,
                'no_expiration': no_expiration_annonces,
                'urgent': urgent_annonces,
                'draft': draft_annonces,
                'important': important_annonces,
            }
        })
    
    # Pour l'affichage HTML normal
    context = {
        'page_obj': page_obj,
        'total_annonces': total_annonces,
        'active_annonces': active_annonces,
        'expired_annonces': expired_annonces,
        'no_expiration_annonces': no_expiration_annonces,
        'urgent_annonces': urgent_annonces,
        'draft_annonces': draft_annonces,
        'important_annonces': important_annonces,
        'types': Annonce.TYPE_CHOICES,
        'search_query': search_query,
        'status_filter': status_filter,  # Important pour garder le filtre actif
        'type_filter': type_filter,      # Important pour garder le filtre actif
        'now': now,  # Pour afficher la date actuelle dans le template
    }
    return render(request, 'annonces/liste_annonces.html', context)

 
# @login_required
# @user_passes_test(can_manage_annonces)
# def liste_annonces(request):
#     """Liste toutes les annonces avec filtres"""
#     annonces = Annonce.objects.all().order_by('-date_publication')
    
#     # Récupérer tous les paramètres
#     type_filter = request.GET.get('type')
#     status_filter = request.GET.get('status')
#     search_query = request.GET.get('search', '')
    
#     # Appliquer les filtres (pour requêtes normales ET AJAX)
#     if type_filter:
#         annonces = annonces.filter(type_annonce=type_filter)
    
#     if status_filter == 'active':
#         annonces = annonces.filter(est_publie=True, date_expiration__gt=timezone.now())
#     elif status_filter == 'expired':
#         annonces = annonces.filter(date_expiration__lt=timezone.now())
#     elif status_filter == 'draft':
#         annonces = annonces.filter(est_publie=False)
    
#     # APPLIQUER LA RECHERCHE POUR LES DEUX TYPES DE REQUÊTES
#     if search_query:
#         annonces = annonces.filter(
#             Q(titre__icontains=search_query) |  # Titre = le plus important
#             Q(contenu__icontains=search_query) |  # Contenu = deuxième important
#             Q(type_annonce__icontains=search_query) |  # Type d'annonce
#             Q(faculte__nom__icontains=search_query)  # Faculté concernée
#         ).distinct()
    
#     # Pagination (uniquement pour requêtes normales)
#     paginator = Paginator(annonces, 15)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     # Si requête AJAX, retourner JSON
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         annonces_data = []
#         for annonce in annonces[:50]:  # Limiter à 50 résultats pour performance
#             annonces_data.append({
#                 'id': annonce.id,
#                 'titre': annonce.titre,
#                 'type': annonce.get_type_annonce_display(),
#                 'type_code': annonce.type_annonce,
#                 'date_publication': annonce.date_publication.strftime('%d/%m/%Y %H:%M'),
#                 'est_publie': annonce.est_publie,
#                 'est_active': annonce.est_active,
#                 'est_important': annonce.est_important,
#                 'faculte': annonce.faculte.nom if annonce.faculte else None,
#                 'auteur': annonce.auteur.get_full_name() if annonce.auteur else 'Inconnu',
#                 'edit_url': reverse('academics:editer_annonce', args=[annonce.pk]),
#             })
        
#         return JsonResponse({
#             'success': True,
#             'annonces': annonces_data,
#             'total': annonces.count(),
#             'search_query': search_query,
#         })
    
#     context = {
#         'page_obj': page_obj,
#         'total_annonces': annonces.count(),
#         'active_annonces': annonces.filter(est_publie=True).count(),
#         'types': Annonce.TYPE_CHOICES,
#         'search_query': search_query,
#     }
#     return render(request, 'annonces/liste_annonces.html', context)

@login_required
@user_passes_test(can_manage_annonces)
def creer_annonce(request):
    """Créer une nouvelle annonce"""
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES)
        if form.is_valid():
            annonce = form.save(commit=False)
            annonce.auteur = request.user
            
            # Vérifier si c'est un brouillon (avec valeur par défaut)
            action = request.POST.get('action', 'publish')
            if action == 'save_draft':
                annonce.est_publie = False
                message_type = 'brouillon'
            else:
                annonce.est_publie = True
                message_type = 'publiée'
            
            # Si aucun destinataire spécifique n'est sélectionné, pour tous
            if not any([
                annonce.destinataire_etudiants,
                annonce.destinataire_professeurs,
                annonce.destinataire_admins
            ]):
                annonce.destinataire_tous = True
            
            annonce.save()
            # ✅ AUDIT seulement si publiée (optionnel)
            if annonce.est_publie:
                audit_creer_annonce(request, annonce)

            messages.success(
                request, 
                f"✅ Annonce « {annonce.titre} » {message_type} avec succès !"
            )
            return redirect('academics:liste_annonces')
        else:
            # Ajouter ce message d'erreur si le formulaire n'est pas valide
            messages.error(
                request,
                "❌ Veuillez corriger les erreurs ci-dessous."
            )
    else:
        form = AnnonceForm()
    
    context = {
        'form': form,
        'action': 'Créer',
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    }
    return render(request, 'annonces/creer_editer_annonce.html', context)


@login_required
@user_passes_test(can_manage_annonces)
def editer_annonce(request, pk):
    """Modifier une annonce existante"""
    annonce = get_object_or_404(Annonce, pk=pk)
    
    # Vérifier que l'utilisateur peut éditer cette annonce
    # (Optionnel: vérifier si admin ou auteur)
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES, instance=annonce)
        if form.is_valid():
            annonce = form.save(commit=False)
            
            # Vérifier si c'est un brouillon
            action = request.POST.get('action', 'publish')
            if action == 'save_draft':
                annonce.est_publie = False
                message_type = 'enregistrée en brouillon'
            else:
                annonce.est_publie = True
                message_type = 'modifiée et publiée'
            
            # Si aucun destinataire spécifique n'est sélectionné, pour tous
            if not any([
                annonce.destinataire_etudiants,
                annonce.destinataire_professeurs,
                annonce.destinataire_admins
            ]):
                annonce.destinataire_tous = True
            
            annonce.save()
            
            messages.success(
                request, 
                f"✅ Annonce « {annonce.titre} » {message_type} avec succès !"
            )
            return redirect('academics:liste_annonces')
        else:
            messages.error(
                request,
                "❌ Veuillez corriger les erreurs ci-dessous."
            )
    else:
        form = AnnonceForm(instance=annonce)
    
    context = {
        'form': form,
        'action': 'Modifier',
        'annonce': annonce,
    }
    return render(request, 'annonces/creer_editer_annonce.html', context)


@login_required
@user_passes_test(can_manage_annonces)
def supprimer_annonce(request, pk):
    """Supprimer une annonce"""
    annonce = get_object_or_404(Annonce, pk=pk)
    
    if request.method == 'POST':
        # ✅ AUDIT: Suppression (AVANT)
        audit_supprimer_annonce(request, annonce)
        
        titre = annonce.titre
        annonce.delete()
        messages.success(request, f"🗑️ Annonce « {titre} » supprimée avec succès !")
        return redirect('academics:liste_annonces')
    
    return render(request, 'annonces/confirmer_suppression.html', {'annonce': annonce})

@login_required
@user_passes_test(can_manage_annonces)
def toggle_publie(request, pk):
    """Basculer l'état de publication d'une annonce"""
    annonce = get_object_or_404(Annonce, pk=pk)
    annonce.est_publie = not annonce.est_publie
    annonce.save()
    
    status = "publiée" if annonce.est_publie else "dépubliée"
    messages.success(
        request, 
        f"🔄 Annonce « {annonce.titre} » {status} avec succès !"
    )
    return redirect('academics:liste_annonces')

def get_annonces_accueil(request):
    """Récupère les annonces à afficher sur la page d'accueil"""
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


def annonces_actives(request):
    """API pour récupérer les annonces actives"""
    annonces = get_annonces_accueil(request)  # Utilise la fonction existante
    # Ou créez votre propre logique pour retourner en JSON
    from django.http import JsonResponse
    import json
    
    annonces_list = []
    for annonce in annonces:
        annonces_list.append({
            'id': annonce.id,
            'titre': annonce.titre,
            'contenu': annonce.contenu,
            'type_annonce': annonce.get_type_annonce_display(),
            'date_publication': annonce.date_publication.strftime('%Y-%m-%d %H:%M'),
            'est_important': annonce.est_important,
        })
    
    return JsonResponse({'annonces': annonces_list})



def annonces_par_type(request, type_annonce):
    """Filtrer les annonces par type"""
    annonces = Annonce.objects.filter(
        type_annonce=type_annonce,
        est_publie=True
    ).order_by('-date_publication')
    
    return render(request, 'annonces/annonces_par_type.html', {
        'annonces': annonces,
        'type_annonce': type_annonce
    })

def annonces_par_faculte(request, faculte_id):
    """Filtrer les annonces par faculté"""
    faculte = get_object_or_404(Faculte, id=faculte_id)
    annonces = Annonce.objects.filter(
        faculte=faculte,
        est_publie=True
    ).order_by('-date_publication')
    
    return render(request, 'annonces/annonces_par_faculte.html', {
        'annonces': annonces,
        'faculte': faculte
    })

def export_annonces(request):
    """Exporter les annonces"""
    import csv
    from django.http import HttpResponse
    
    # Votre logique d'export ici
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="annonces.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Titre', 'Type', 'Date publication', 'Publié'])
    
    annonces = Annonce.objects.all()
    for annonce in annonces:
        writer.writerow([
            annonce.titre,
            annonce.get_type_annonce_display(),
            annonce.date_publication,
            'Oui' if annonce.est_publie else 'Non'
        ])
    
    return response

