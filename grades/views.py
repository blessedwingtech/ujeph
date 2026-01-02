import csv
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Max

from accounts.views import can_access_academique, can_manage_academique, is_admin, permission_required
from grades.utils import STATUT_BROUILLON, STATUT_PUBLIEE, STATUT_REJETEE, STATUT_SOUMISE, STATUTS_MODIFIABLES, calculer_et_stocker_moyennes, reattribuer_cours_etudiant
from .models import HistoriquePromotion, Note, MoyenneSemestre, ReleveDeNotes
from academics.models import Cours, Faculte
from accounts.models import Etudiant, User
# grades/views.py
from django.db.models import Prefetch, Count, Q

# Dans grades/views.py - MODIFIER saisie_notes
from django.utils import timezone
   
from django.utils import timezone
from django.db.models import Count, Q
from .models import Cours, Note, User
from django.core.paginator import Paginator

 

 
# AJOUTEZ CET IMPORT EN HAUT DU FICHIER
from accounts.audit_utils import (
    audit_saisir_notes, audit_soumettre_notes, 
    audit_publier_notes, audit_rejeter_notes,
    audit_action_generique
)
    
# @login_required
# def saisie_notes(request, cours_id):
#     """Professeur: Saisie des notes pour un cours avec restrictions intelligentes"""
#     if request.user.role != User.Role.PROFESSEUR:
#         messages.error(request, "Accès réservé aux professeurs")
#         return redirect('accounts:dashboard')
    
#     cours = get_object_or_404(Cours, id=cours_id, professeur=request.user)
#     etudiants = cours.etudiants_concernes().select_related('user')
    
#     # Récupérer toutes les notes existantes pour ce cours
#     notes_existantes = Note.objects.filter(
#         cours=cours, 
#         created_by=request.user
#     ).select_related('etudiant')
    
#     notes_dict = {note.etudiant_id: note for note in notes_existantes}
    
#     # ✅ ANALYSE DES STATUTS POUR LES RESTRICTIONS
#     notes_soumises = notes_existantes.filter(statut='soumise').exists()
#     notes_publiees = notes_existantes.filter(statut='publiée').exists()
#     notes_rejetees = notes_existantes.filter(statut='rejetée').exists()
#     notes_brouillon = notes_existantes.filter(statut='brouillon').exists()
    
#     # ✅ LOGIQUE DES RESTRICTIONS
#     peut_soumettre = not notes_soumises and (notes_brouillon or notes_rejetees)
#     peut_modifier_brouillons = not notes_soumises
#     toutes_notes_publiees = notes_publiees and not (notes_soumises or notes_brouillon or notes_rejetees)
    
#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         # ✅ VÉRIFICATION DES RESTRICTIONS
#         if action == 'soumettre' and not peut_soumettre:
#             messages.error(request, 
#                 "❌ Impossible de soumettre : certaines notes sont déjà en attente de validation "
#                 "ou aucune note n'est prête à être soumise."
#             )
#             return redirect('grades:saisie_notes', cours_id=cours_id)
        
#         if action == 'enregistrer' and not peut_modifier_brouillons:
#             messages.error(request, 
#                 "❌ Impossible de modifier : des notes sont en attente de validation. "
#                 "Veuillez attendre la validation de l'admin ou annuler la soumission."
#             )
#             return redirect('grades:saisie_notes', cours_id=cours_id)
        
#         # Traitement des notes
#         for etudiant in etudiants:
#             note_value = request.POST.get(f'note_{etudiant.id}')
            
#             if not note_value:
#                 continue
                
#             try:
#                 note_value = float(note_value)
#                 if not (0 <= note_value <= 100):
#                     messages.error(request, f"Note invalide pour {etudiant.user.get_full_name()}")
#                     continue
#             except (ValueError, TypeError):
#                 messages.error(request, f"Format de note invalide pour {etudiant.user.get_full_name()}")
#                 continue
            
#             # Déterminer le statut selon l'action et les restrictions
#             if action == 'soumettre' and peut_soumettre:
#                 nouveau_statut = 'soumise'
#             elif action == 'enregistrer' and peut_modifier_brouillons:
#                 nouveau_statut = 'brouillon'
#             else:
#                 continue  # Ne pas traiter si restriction activée
            
#             note, created = Note.objects.get_or_create(
#                 etudiant=etudiant,
#                 cours=cours,
#                 type_evaluation='examen',
#                 defaults={
#                     'valeur': note_value,
#                     'created_by': request.user,
#                     'statut': nouveau_statut
#                 }
#             )
            
#             if not created:
#                 # Vérifier si la note peut être modifiée
#                 if not note.peut_modifier_par(request.user):
#                     messages.error(request, 
#                         f"Note de {etudiant.user.get_full_name()} non modifiable "
#                         f"(statut: {note.get_statut_display()})"
#                     )
#                     continue
                
#                 # Mettre à jour la note
#                 note.valeur = note_value
#                 note.statut = nouveau_statut
                
#                 if action == 'soumettre':
#                     note.date_soumission = timezone.now()
#                     note.motif_rejet = None  # Reset le motif si re-soumission
                
#                 note.save()
        
#         # Messages de confirmation
#         if action == 'soumettre':
#             messages.success(request, 
#                 "✅ Notes soumises pour validation avec succès! "
#                 "Vous ne pourrez plus les modifier avant la validation de l'admin."
#             )
#         elif action == 'enregistrer':
#             messages.success(request, "💾 Notes enregistrées en brouillon!")
        
#         return redirect('grades:saisie_notes', cours_id=cours_id)
    
#     context = {
#         'cours': cours,
#         'etudiants': etudiants,
#         'notes_dict': notes_dict,
#         # ✅ NOUVEAUX CONTEXTES POUR LES RESTRICTIONS
#         'notes_soumises': notes_soumises,
#         'notes_publiees': notes_publiees,
#         'notes_rejetees': notes_rejetees,
#         'notes_brouillon': notes_brouillon,
#         'peut_soumettre': peut_soumettre,
#         'peut_modifier_brouillons': peut_modifier_brouillons,
#         'toutes_notes_publiees': toutes_notes_publiees,
#     }
#     return render(request, 'grades/saisie_notes.html', context)

 
#----lavant dernier vue saisie not
# @login_required
# def saisie_notes(request, cours_id):
#     """
#     Vue pour la saisie des notes avec validation par bloc
#     """
#     if request.user.role != User.Role.PROFESSEUR:
#         messages.error(request, "❌ Accès réservé aux professeurs")
#         return redirect('accounts:dashboard')

#     # Récupérer le cours
#     cours = get_object_or_404(Cours, id=cours_id, professeur=request.user)
    
#     # Récupérer les étudiants
    
#     #etudiants = cours.etudiants_concernes().select_related('user')
#     etudiants = Etudiant.objects.filter(
#             inscriptions__cours=cours
#         ).select_related('user').distinct()
    
#     # Récupérer les notes existantes
#     notes = Note.objects.filter(
#         cours=cours,
#         created_by=request.user
#     ).select_related('etudiant')
    
#     notes_dict = {n.etudiant_id: n for n in notes}
    
#     # ANALYSE DES STATUTS
#     aucune_note = not notes.exists()
    
#     # Vérifier les différents statuts présents
#     statuts_presents = set(notes.values_list('statut', flat=True))
    
#     # Variables pour le template
#     notes_soumises = STATUT_SOUMISE in statuts_presents
#     notes_publiees = STATUT_PUBLIEE in statuts_presents
#     notes_rejetees = STATUT_REJETEE in statuts_presents
#     notes_brouillon = STATUT_BROUILLON in statuts_presents
    
#     # Vérifier si tous les étudiants ont une note
#     tous_ont_note = etudiants.count() == notes.count()
    
#     # LOGIQUE DE PERMISSION CORRIGÉE
#     # 1. Peut modifier si AUCUNE note n'est soumise ou publiée
#     peut_modifier = not (notes_soumises or notes_publiees)
    
#     # 2. Peut soumettre si :
#     #    - On peut modifier (pas de notes soumises/publiées)
#     #    - Tous les étudiants ont une note
#     #    - Il y a au moins une note
#     peut_soumettre = peut_modifier and tous_ont_note and notes.exists()
    
#     # 3. Toutes notes publiées ?
#     toutes_notes_publiees = (
#         notes_publiees and 
#         not notes_soumises and 
#         not notes_rejetees and 
#         not notes_brouillon and
#         tous_ont_note
#     )
    
#     # TRAITEMENT DU FORMULAIRE POST - CORRECTION IMPORTANTE
#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         print(f"Action reçue: {action}")  # DEBUG
        
#         # VALIDATION DES PERMISSIONS
#         if action == 'soumettre':
#             if not peut_soumettre:
#                 if notes_soumises:
#                     messages.error(request, 
#                         "❌ IMPOSSIBLE DE SOUMETTRE : Les notes sont déjà soumises pour validation."
#                     )
#                 elif notes_publiees:
#                     messages.error(request, 
#                         "❌ IMPOSSIBLE DE SOUMETTRE : Les notes sont déjà publiées."
#                     )
#                 elif not tous_ont_note:
#                     missing_count = etudiants.count() - notes.count()
#                     messages.error(request, 
#                         f"❌ IMPOSSIBLE DE SOUMETTRE : {missing_count} étudiant(s) sans note."
#                     )
#                 return redirect('grades:saisie_notes', cours_id=cours_id)
        
#         if action == 'enregistrer' and not peut_modifier:
#             if notes_soumises:
#                 messages.error(request, "❌ IMPOSSIBLE DE MODIFIER : Notes en attente de validation.")
#             elif notes_publiees:
#                 messages.error(request, "❌ IMPOSSIBLE DE MODIFIER : Notes déjà publiées.")
#             return redirect('grades:saisie_notes', cours_id=cours_id)
        
#         # Déterminer le nouveau statut
#         nouveau_statut = STATUT_SOUMISE if action == 'soumettre' else STATUT_BROUILLON
        
#         print(f"Nouveau statut: {nouveau_statut}")  # DEBUG
        
#         notes_traitees = 0
#         erreurs = []
        
#         for etudiant in etudiants:
#             valeur_str = request.POST.get(f'note_{etudiant.id}')
            
#             # Si pas de valeur et qu'on soumet, c'est une erreur
#             if action == 'soumettre' and not valeur_str:
#                 erreurs.append(f"{etudiant.user.get_full_name()}: Note manquante")
#                 continue
            
#             # Si pas de valeur et enregistrement brouillon, on peut passer
#             if action == 'enregistrer' and not valeur_str:
#                 continue
            
#             # Validation de la valeur
#             try:
#                 valeur = float(valeur_str)
#                 if not 0 <= valeur <= 100:
#                     raise ValueError(f"Note invalide: {valeur}/100")
#             except (ValueError, TypeError) as e:
#                 erreurs.append(f"{etudiant.user.get_full_name()}: {str(e)}")
#                 continue
            
#             # CRÉATION/MISE À JOUR DE LA NOTE - CORRECTION CRITIQUE
#             try:
#                 # Essayer de récupérer la note existante
#                 note = Note.objects.get(
#                     etudiant=etudiant,
#                     cours=cours,
#                     type_evaluation='examen'
#                 )
                
#                 # Vérifier si on peut modifier cette note
#                 if note.statut in [STATUT_SOUMISE, STATUT_PUBLIEE]:
#                     erreurs.append(f"{etudiant.user.get_full_name()}: Note non modifiable")
#                     continue
                
#                 # Mettre à jour la note existante
#                 note.valeur = valeur
#                 note.statut = nouveau_statut
#                 note.motif_rejet = None  # Réinitialiser le motif
                
#                 if action == 'soumettre':
#                     note.date_soumission = timezone.now()
#                 else:
#                     note.date_soumission = None
                
#                 note.save()
                
#             except Note.DoesNotExist:
#                 # Créer une nouvelle note
#                 note = Note.objects.create(
#                     etudiant=etudiant,
#                     cours=cours,
#                     type_evaluation='examen',
#                     valeur=valeur,
#                     created_by=request.user,
#                     statut=nouveau_statut,
#                     motif_rejet=None,
#                     date_soumission=timezone.now() if action == 'soumettre' else None
#                 )
            
#             notes_traitees += 1
#         # ✅ AUDIT selon l'action
#         if notes_traitees > 0:
#             if action == 'soumettre':
#                 audit_soumettre_notes(request, cours, notes_traitees)
#             else:  # enregistrer
#                 audit_saisir_notes(request, cours, notes_traitees)
#         # Afficher les messages d'erreur
#         if erreurs:
#             for erreur in erreurs[:3]:
#                 messages.error(request, erreur)
        
#         # MESSAGES DE CONFIRMATION
#         if notes_traitees > 0:
#             if action == 'soumettre':
#                 # VÉRIFIER QUE LE STATUT EST BIEN SOUMIS
#                 notes_soumises_verif = Note.objects.filter(
#                     cours=cours,
#                     created_by=request.user,
#                     statut=STATUT_SOUMISE
#                 ).count()
                
#                 messages.success(request, 
#                     f"✅ {notes_traitees} NOTE(S) SOUMISE(S) AVEC SUCCÈS !"
#                 )
#                 messages.warning(request, 
#                     f"Statut confirmé: {notes_soumises_verif} note(s) avec statut 'soumise'"
#                 )
#             else:  # enregistrer
#                 messages.success(request, 
#                     f"💾 {notes_traitees} NOTE(S) ENREGISTRÉE(S) EN BROUILLON"
#                 )
        
#         return redirect('grades:saisie_notes', cours_id=cours_id)
#     nb_sans_note = etudiants.count() - notes.count()

#     # Préparer le contexte
#     context = {
#         'nb_sans_note': nb_sans_note,
#         'cours': cours,
#         'etudiants': etudiants,
#         'notes_dict': notes_dict,
#         'peut_modifier': peut_modifier,
#         'peut_soumettre': peut_soumettre,
#         'tous_ont_note': tous_ont_note,
#         'aucune_note': aucune_note,
#         'notes_soumises': notes_soumises,
#         'toutes_notes_publiees': toutes_notes_publiees,
#         'notes_rejetees': notes_rejetees,
#         'notes_brouillon': notes_brouillon,
#     }
    
#     return render(request, 'grades/saisie_notes.html', context)

@login_required
def saisie_notes(request, cours_id):
    """
    Vue pour la saisie des notes avec validation par bloc
    """
    if request.user.role != User.Role.PROFESSEUR:
        messages.error(request, "❌ Accès réservé aux professeurs")
        return redirect('accounts:dashboard')

    # Récupérer le cours
    cours = get_object_or_404(Cours, id=cours_id, professeur=request.user)
    
    # Récupérer les étudiants
    etudiants = Etudiant.objects.filter(
        inscriptions__cours=cours
    ).select_related('user').distinct().order_by('user__last_name', 'user__first_name')
    
    # ============ TRAITEMENT DU FORMULAIRE POST ============
    if request.method == 'POST':
        action = request.POST.get('action')
        
        print(f"=== POST - Action: {action} ===")
        
        # Récupérer les notes existantes AVANT traitement
        notes_existantes = Note.objects.filter(
            cours=cours,
            created_by=request.user
        ).select_related('etudiant')
        notes_dict_existantes = {n.etudiant_id: n for n in notes_existantes}
        
        # ANALYSE DES STATUTS (avant traitement)
        statuts_presents = set(notes_existantes.values_list('statut', flat=True))
        notes_soumises_avant = STATUT_SOUMISE in statuts_presents
        notes_publiees_avant = STATUT_PUBLIEE in statuts_presents
        
        # Vérifier si tous les étudiants ont une note (avant)
        tous_ont_note_avant = etudiants.count() == notes_existantes.count()
        
        # VALIDATION DES PERMISSIONS
        if action == 'soumettre':
            if notes_soumises_avant:
                messages.error(request, 
                    "❌ IMPOSSIBLE DE SOUMETTRE : Les notes sont déjà soumises pour validation."
                )
                return redirect('grades:saisie_notes', cours_id=cours_id)
            elif notes_publiees_avant:
                messages.error(request, 
                    "❌ IMPOSSIBLE DE SOUMETTRE : Les notes sont déjà publiées."
                )
                return redirect('grades:saisie_notes', cours_id=cours_id)
            elif not tous_ont_note_avant:
                missing_count = etudiants.count() - notes_existantes.count()
                messages.error(request, 
                    f"❌ IMPOSSIBLE DE SOUMETTRE : {missing_count} étudiant(s) sans note."
                )
                return redirect('grades:saisie_notes', cours_id=cours_id)
        
        if action == 'enregistrer':
            if notes_soumises_avant:
                messages.error(request, "❌ IMPOSSIBLE DE MODIFIER : Notes en attente de validation.")
                return redirect('grades:saisie_notes', cours_id=cours_id)
            elif notes_publiees_avant:
                messages.error(request, "❌ IMPOSSIBLE DE MODIFIER : Notes déjà publiées.")
                return redirect('grades:saisie_notes', cours_id=cours_id)
        
        # Déterminer le nouveau statut
        nouveau_statut = STATUT_SOUMISE if action == 'soumettre' else STATUT_BROUILLON
        
        notes_traitees = 0
        erreurs = []
        
        for etudiant in etudiants:
            # IMPORTANT: Utiliser .get() avec valeur par défaut et .strip()
            valeur_str = request.POST.get(f'note_{etudiant.id}', '').strip()
            
            print(f"  Étudiant {etudiant.id} ({etudiant.user.get_full_name()}): '{valeur_str}'")
            
            # ===== LOGIQUE POUR BROUILLON =====
            if action == 'enregistrer':
                # Si champ vide ou None
                if not valeur_str:
                    # Vérifier si une note existe déjà
                    note_existante = notes_dict_existantes.get(etudiant.id)
                    if note_existante:
                        # Si c'est un brouillon, on peut le supprimer
                        if note_existante.statut == STATUT_BROUILLON:
                            note_existante.delete()
                            print(f"    -> Brouillon supprimé")
                        else:
                            print(f"    -> Note existante gardée (statut: {note_existante.statut})")
                    continue
            
            # ===== LOGIQUE POUR SOUMISSION =====
            if action == 'soumettre' and not valeur_str:
                erreurs.append(f"{etudiant.user.get_full_name()}: Note manquante")
                continue
            
            # Validation de la valeur
            try:
                # Remplacer virgule par point pour parsing
                valeur_str_clean = valeur_str.replace(',', '.')
                valeur = float(valeur_str_clean)
                if not 0 <= valeur <= 100:
                    raise ValueError(f"Note invalide: {valeur}/100")
            except (ValueError, TypeError) as e:
                erreurs.append(f"{etudiant.user.get_full_name()}: Note invalide")
                continue
            
            # ===== CRÉATION/MISE À JOUR DE LA NOTE =====
            try:
                # Essayer de récupérer la note existante
                note = Note.objects.get(
                    etudiant=etudiant,
                    cours=cours,
                    type_evaluation='examen'
                )
                
                # Vérifier si on peut modifier cette note
                if note.statut in [STATUT_SOUMISE, STATUT_PUBLIEE]:
                    erreurs.append(f"{etudiant.user.get_full_name()}: Note non modifiable (déjà {note.get_statut_display()})")
                    continue
                
                # Mettre à jour la note existante
                note.valeur = valeur
                note.statut = nouveau_statut
                note.motif_rejet = None
                
                if action == 'soumettre':
                    note.date_soumission = timezone.now()
                else:
                    note.date_soumission = None
                
                note.save()
                print(f"    -> Note mise à jour: {valeur}")
                
            except Note.DoesNotExist:
                # Créer une nouvelle note
                note = Note.objects.create(
                    etudiant=etudiant,
                    cours=cours,
                    type_evaluation='examen',
                    valeur=valeur,
                    created_by=request.user,
                    statut=nouveau_statut,
                    motif_rejet=None,
                    date_soumission=timezone.now() if action == 'soumettre' else None
                )
                print(f"    -> Nouvelle note créée: {valeur}")
            
            notes_traitees += 1
        
        # ✅ AUDIT selon l'action
        if notes_traitees > 0:
            if action == 'soumettre':
                audit_soumettre_notes(request, cours, notes_traitees)
            else:
                audit_saisir_notes(request, cours, notes_traitees)
        
        # Afficher les messages d'erreur
        if erreurs:
            for erreur in erreurs[:5]:
                messages.error(request, erreur)
        
        # MESSAGES DE CONFIRMATION
        if notes_traitees > 0:
            if action == 'soumettre':
                messages.success(request, 
                    f"✅ {notes_traitees} NOTE(S) SOUMISE(S) AVEC SUCCÈS !"
                )
            else:
                messages.success(request, 
                    f"💾 {notes_traitees} NOTE(S) ENREGISTRÉE(S) EN BROUILLON"
                )
        elif action == 'enregistrer' and not erreurs:
            messages.info(request, 
                "📝 Aucune modification (champs vides ou notes supprimées)"
            )
        
        print(f"=== FIN POST - {notes_traitees} notes traitées ===")
        return redirect('grades:saisie_notes', cours_id=cours_id)
    
    # ============ PARTIE GET (après redirection ou affichage initial) ============
    print(f"=== GET - Rechargement de la page ===")
    
    # IMPORTANT: Toujours recharger les notes fraîches depuis la base
    notes = Note.objects.filter(
        cours=cours,
        created_by=request.user
    ).select_related('etudiant')
    
    # Créer le dictionnaire pour le template
    notes_dict = {n.etudiant_id: n for n in notes}
    
    # Debug: Afficher ce qu'on a dans notes_dict
    print(f"Nombre de notes dans notes_dict: {len(notes_dict)}")
    for etudiant_id, note in notes_dict.items():
        print(f"  Étudiant {etudiant_id}: {note.valeur} (statut: {note.statut})")
    
    # ANALYSE DES STATUTS
    aucune_note = not notes.exists()
    statuts_presents = set(notes.values_list('statut', flat=True))
    
    # Variables pour le template
    notes_soumises = STATUT_SOUMISE in statuts_presents
    notes_publiees = STATUT_PUBLIEE in statuts_presents
    notes_rejetees = STATUT_REJETEE in statuts_presents
    notes_brouillon = STATUT_BROUILLON in statuts_presents
    
    # Vérifier si tous les étudiants ont une note
    tous_ont_note = etudiants.count() == notes.count()
    
    # LOGIQUE DE PERMISSION
    peut_modifier = not (notes_soumises or notes_publiees)
    peut_soumettre = peut_modifier and tous_ont_note and notes.exists()
    
    toutes_notes_publiees = (
        notes_publiees and 
        not notes_soumises and 
        not notes_rejetees and 
        not notes_brouillon and
        tous_ont_note
    )
    
    nb_sans_note = etudiants.count() - notes.count()
    
    print(f"=== FIN GET - Contexte prêt ===")

    # Préparer le contexte
    context = {
        'nb_sans_note': nb_sans_note,
        'cours': cours,
        'etudiants': etudiants,
        'notes_dict': notes_dict,  # Dictionnaire FRAIS
        'peut_modifier': peut_modifier,
        'peut_soumettre': peut_soumettre,
        'tous_ont_note': tous_ont_note,
        'aucune_note': aucune_note,
        'notes_soumises': notes_soumises,
        'toutes_notes_publiees': toutes_notes_publiees,
        'notes_rejetees': notes_rejetees,
        'notes_brouillon': notes_brouillon,
    }
    
    return render(request, 'grades/saisie_notes.html', context)

# @login_required
# @user_passes_test(is_admin)
# def validation_notes(request):
#     """Admin: Validation des notes soumises avec motif de rejet"""
#     if request.user.role != User.Role.ADMIN:
#         messages.error(request, "Accès réservé aux administrateurs")
#         return redirect('accounts:dashboard')
    
#     notes_soumises = Note.objects.filter(statut='soumise').select_related(
#         'cours', 'etudiant__user', 'created_by'
#     )
    
#     if request.method == 'POST':
#         note_id = request.POST.get('note_id')
#         action = request.POST.get('action')
#         motif_rejet = request.POST.get('motif_rejet', '').strip()
        
#         if note_id and action:
#             try:
#                 note = Note.objects.get(id=note_id, statut='soumise')
                
#                 if action == 'publier':
#                     note.publier()
#                     messages.success(request, 
#                         f"✅ Note de {note.etudiant.user.get_full_name()} publiée avec succès!"
#                     )
                    
#                 elif action == 'rejeter':
#                     if not motif_rejet:
#                         messages.error(request, 
#                             "❌ Veuillez fournir un motif de rejet."
#                         )
#                         return redirect('grades:validation_notes')
                    
#                     note.rejeter(motif_rejet)
#                     messages.warning(request, 
#                         f"❌ Note de {note.etudiant.user.get_full_name()} rejetée. "
#                         f"Motif: {motif_rejet}"
#                     )
                    
#             except Note.DoesNotExist:
#                 messages.error(request, "❌ Note non trouvée ou déjà traitée")
        
#         return redirect('grades:validation_notes')
    
#     context = {
#         'notes_soumises': notes_soumises,
#     }
#     return render(request, 'grades/validation_notes.html', context)

 



@login_required
#@permission_required(can_access_academique, redirect_url='accounts:dashboard')
@permission_required(is_admin)
def validation_notes(request):
    """
    Admin: Liste des cours avec notes soumises
    """
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "❌ Accès réservé aux administrateurs")
        return redirect('accounts:dashboard')
    
    # Récupérer les cours qui ont des notes soumises
    cours_ids = Note.objects.filter(
        statut=STATUT_SOUMISE
    ).values_list('cours_id', flat=True).distinct()
    
    # Annoter avec le nombre de notes soumises
    cours_list = Cours.objects.filter(id__in=cours_ids).annotate(
        notes_soumises_count=Count('note', filter=Q(note__statut=STATUT_SOUMISE))
    ).select_related('professeur', 'faculte')
    
    # Ajouter la date de dernière soumission pour chaque cours
    for cours in cours_list:
        derniere_note = cours.note_set.filter(
            statut=STATUT_SOUMISE
        ).order_by('-date_soumission').first()
        cours.date_derniere_soumission = derniere_note.date_soumission if derniere_note else None
    
    context = {
        'cours_soumis': cours_list,
    }
    return render(request, 'grades/validation_notes.html', context)

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def traiter_cours_notes(request, cours_id):
    """
    Admin: Traiter toutes les notes d'un cours (version améliorée)
    """
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "❌ Accès réservé aux administrateurs")
        return redirect('accounts:dashboard')
    
    cours = get_object_or_404(Cours, id=cours_id)
    
    # Récupérer uniquement les notes soumises
    notes = Note.objects.filter(
        cours=cours,
        statut=STATUT_SOUMISE
    ).select_related('etudiant__user')
    
    if not notes.exists():
        messages.error(request, "❌ Ce cours n'a pas de notes en attente de validation.")
        return redirect('grades:validation_notes')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        motif = request.POST.get('motif_rejet', '').strip()
        
        if action == 'publier':
            # Publier toutes les notes
            # ✅ AUDIT: Publication
            audit_publier_notes(request, cours, notes.count(), request.user)
            notes.update(
                statut=STATUT_PUBLIEE,
                date_validation=timezone.now()
            )
            
            messages.success(request, 
                f"✅ {notes.count()} NOTE(S) PUBLIÉE(S) !\n"
                f"Les notes du cours '{cours.intitule}' sont maintenant visibles par les étudiants."
            )
            
        elif action == 'rejeter':
            if not motif:
                messages.error(request, "❌ Vous devez fournir un motif de rejet.")
                return redirect('grades:traiter_cours_notes', cours_id=cours_id)
            # ✅ AUDIT: Rejet
            audit_rejeter_notes(request, cours, notes.count(), motif)
            # Rejeter toutes les notes avec le même motif
            updated_count=notes.update(
                statut=STATUT_REJETEE,
                motif_rejet=motif
            )
            
            messages.warning(request, 
                f"❌ {updated_count} NOTE(S) REJETÉE(S)\n"
                f"Motif: {motif}"
            )
        
        return redirect('grades:validation_notes')
    
    context = {
        'cours': cours,
        'notes': notes,
    }
    return render(request, 'grades/traiter_cours.html', context)



@login_required
def consulter_notes_etudiant(request):
    """Étudiant: Consultation de ses notes publiées avec historique par année"""
    if request.user.role != User.Role.ETUDIANT or not hasattr(request.user, 'etudiant'):
        messages.error(request, "❌ Accès réservé aux étudiants")
        return redirect('accounts:dashboard')
    
    etudiant = request.user.etudiant
    semestre_actuel = etudiant.semestre_courant
    niveau_actuel = etudiant.niveau
    faculte_etudiant = etudiant.faculte
    
    # Déterminer l'année académique courante
    from django.utils import timezone
    maintenant = timezone.now()
    annee_courante = f"{maintenant.year}-{maintenant.year+1}"
    
    # 1. Récupérer TOUTES les notes publiées, groupées par année
    notes_publiees = Note.objects.filter(
        etudiant=etudiant,
        statut='publiée'
    ).select_related('cours').order_by(
        '-annee_academique',
        'cours__semestre',
        'cours__intitule'
    )
    
    # 2. Organiser les notes par année académique
    notes_par_annee = {}
    for note in notes_publiees:
        annee = note.annee_academique or annee_courante
        
        if annee not in notes_par_annee:
            notes_par_annee[annee] = {'S1': [], 'S2': []}
        
        notes_par_annee[annee][note.cours.semestre].append(note)
    
    # 3. Calculer les moyennes pour chaque année/semestre
    def calculer_moyenne(notes_list):
        if not notes_list:
            return None
        total = sum(note.valeur for note in notes_list)
        return round(total / len(notes_list), 2)
    
    moyennes_par_annee = {}
    for annee, semestres in notes_par_annee.items():
        moy_s1 = calculer_moyenne(semestres['S1'])
        moy_s2 = calculer_moyenne(semestres['S2'])
        
        moyenne_generale = None
        if moy_s1 is not None and moy_s2 is not None:
            moyenne_generale = round((moy_s1 + moy_s2) / 2, 2)
        # elif moy_s2 is not None:
        #     moyenne_generale = moy_s2
        # elif moy_s1 is not None:
        #     moyenne_generale = moy_s1
        
        moyennes_par_annee[annee] = {
            'S1': moy_s1,
            'S2': moy_s2,
            'generale': moyenne_generale
        }
    
    # 4. Récupérer l'historique des promotions
    from .models import HistoriquePromotion
    historique_promotions = HistoriquePromotion.objects.filter(
        etudiant=etudiant
    ).order_by('-annee_academique', '-date_promotion')
    
    # 5. Situation actuelle
    situation_actuelle = {
        'annee_academique': annee_courante,
        'semestre_courant': semestre_actuel,
        'niveau_courant': niveau_actuel,
        'statut': etudiant.statut_academique,
        'faculte': faculte_etudiant.nom,
    }
    
    # 6. Cours du semestre actuel
    from academics.models import Cours
    cours_semestre_actuel = Cours.objects.filter(
        faculte=faculte_etudiant,
        niveau=niveau_actuel,
        semestre=semestre_actuel
    ).select_related('professeur__professeur')
    
    # 7. Moyennes pour l'année courante
    moyenne_generale = moyennes_par_annee.get(annee_courante, {}).get('generale')
    moyenne_s1 = moyennes_par_annee.get(annee_courante, {}).get('S1')
    moyenne_s2 = moyennes_par_annee.get(annee_courante, {}).get('S2')
    
    # 8. Récupérer les notes pour chaque cours du semestre actuel
        # 8. Récupérer les notes pour chaque cours du semestre actuel - CORRIGÉ
    cours_avec_notes = []
    for cours in cours_semestre_actuel:
        note_trouvee = None
        
        # Chercher dans notes_par_annee[annee_courante][semestre_actuel]
        if annee_courante in notes_par_annee:
            notes_semestre = notes_par_annee[annee_courante].get(semestre_actuel, [])
            for note in notes_semestre:
                if note.cours.id == cours.id:
                    note_trouvee = note
                    break
        
        cours_avec_notes.append({
            'cours': cours,
            'note': note_trouvee,
            'est_note': note_trouvee is not None
        })

    # DEBUG supplémentaire
    print(f"\n=== DEBUG COURS AVEC NOTES (CORRIGÉ) ===")
    print(f"Année courante: {annee_courante}")
    print(f"Semestre actuel: {semestre_actuel}")
    for item in cours_avec_notes:
        note = item['note']
        print(f"Cours: {item['cours'].code}, Note: {note.valeur if note else 'Aucune'}")
    
    # 9. Calculer la moyenne du semestre actuel (nouveau)
    notes_semestre_actuel = []
    for item in cours_avec_notes:
        if item['note'] and item['note'].cours.semestre == semestre_actuel:
            notes_semestre_actuel.append(item['note'])
    
    moyenne_semestre_actuel = None
    if notes_semestre_actuel:
        moyenne_semestre_actuel = sum(n.valeur for n in notes_semestre_actuel) / len(notes_semestre_actuel)
    
    # 10. Statistiques du semestre basées sur 70/100
    cours_valides_70 = sum(1 for n in notes_semestre_actuel if n.valeur >= 70)
    cours_echec_70 = sum(1 for n in notes_semestre_actuel if n.valeur < 70)
    cours_attente = cours_semestre_actuel.count() - len(notes_semestre_actuel)
    
    context = {
        'etudiant': etudiant,
        'situation_actuelle': situation_actuelle,
        'notes_par_annee': notes_par_annee,
        'moyennes_par_annee': moyennes_par_annee,
        'historique_promotions': historique_promotions,
        'cours_avec_notes': cours_avec_notes,
        'cours_semestre_actuel': cours_semestre_actuel,
        'annee_courante': annee_courante,
        'semestre_actuel': semestre_actuel,
        'moyenne_generale': moyenne_generale,
        'moyenne_s1': moyenne_s1,
        'moyenne_s2': moyenne_s2,
        'moyenne_semestre_actuel': moyenne_semestre_actuel,
        'cours_valides_70': cours_valides_70,
        'cours_echec_70': cours_echec_70,
        'cours_attente': cours_attente,
        'count_s1': len(notes_par_annee.get(annee_courante, {}).get('S1', [])),
        'count_s2': len(notes_par_annee.get(annee_courante, {}).get('S2', [])),
        'total_notes': notes_publiees.count(),
        'faculte': faculte_etudiant,
    }
    
    return render(request, 'grades/consulter_notes_etudiant.html', context)

# @login_required
# def consulter_notes_etudiant(request):
#     """Étudiant: Consultation de ses notes publiées"""
#     if request.user.role != User.Role.ETUDIANT or not hasattr(request.user, 'etudiant'):
#         messages.error(request, "❌ Accès réservé aux étudiants")
#         return redirect('accounts:dashboard')
    
#     etudiant = request.user.etudiant
    
#     # Récupérer les notes publiées
#     notes_publiees = Note.objects.filter(
#         etudiant=etudiant,
#         statut='publiée'
#     ).select_related(
#         'cours', 
#         'cours__faculte',
#         'created_by'
#     ).order_by(
#         'cours__semestre', 
#         'cours__intitule'
#     )
    
#     # Calcul des moyennes par semestre (avec vos champs existants)
#     moyenne_s1 = None
#     moyenne_s2 = None
    
#     # Pour S1
#     # Calcul des moyennes par semestre (CORRECTION)  
#     notes_s1 = notes_publiees.filter(cours__semestre='S1')
#     if notes_s1.exists():
#         # ✅ CORRECTION : Calcul simple (plus de crédits)
#         total_s1 = sum(float(note.valeur) for note in notes_s1)
#         moyenne_s1 = total_s1 / notes_s1.count()  # Moyenne arithmétique simple
#     else:
#         moyenne_s1 = None

#     # Pour S2
#     notes_s2 = notes_publiees.filter(cours__semestre='S2')
#     if notes_s2.exists():
#         # ✅ CORRECTION : Calcul simple (plus de crédits)
#         total_s2 = sum(float(note.valeur) for note in notes_s2)
#         moyenne_s2 = total_s2 / notes_s2.count()  # Moyenne arithmétique simple
#     else:
#         moyenne_s2 = None

#     # Calcul de la moyenne générale (seulement si S2 disponible)
#     moyenne_generale = None
#     if moyenne_s1 is not None and moyenne_s2 is not None:
#         moyenne_generale = (moyenne_s1 + moyenne_s2) / 2
#     elif moyenne_s2 is not None:
#         moyenne_generale = moyenne_s2  # Seul S2 disponible
    
#     # Compter les notes par semestre
#     count_s1 = notes_s1.count()
#     count_s2 = notes_s2.count()
    
#     context = {
#         'etudiant': etudiant,
#         'notes_publiees': notes_publiees,
#         'moyenne_s1': moyenne_s1,
#         'moyenne_s2': moyenne_s2,
#         'moyenne_generale': moyenne_generale,
#         'count_s1': count_s1,
#         'count_s2': count_s2,
#         'total_notes': notes_publiees.count(),
#     }
#     return render(request, 'grades/consulter_notes_etudiant.html', context)


# grades/views.py
# grades/views.py

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def gestion_notes_publiees(request):
    """
    Admin: Liste des cours avec notes PUBLIÉES (pour remise en brouillon)
    """
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "❌ Accès réservé aux administrateurs")
        return redirect('accounts:dashboard')
    
    # Filtrer uniquement les cours avec des notes PUBLIÉES
    cours_ids = Note.objects.filter(
        statut=STATUT_PUBLIEE  # ou 'publiée' selon votre modèle
    ).values_list('cours_id', flat=True).distinct()
    
    # Annoter avec le nombre de notes publiées
    cours_list = Cours.objects.filter(id__in=cours_ids).annotate(
        notes_publiees_count=Count('note', filter=Q(note__statut=STATUT_PUBLIEE))
    ).select_related('professeur', 'faculte')
    
    # Ajouter la date de publication pour chaque cours
    for cours in cours_list:
        derniere_publication = cours.note_set.filter(
            statut=STATUT_PUBLIEE
        ).order_by('-date_validation').first()
        cours.date_derniere_publication = derniere_publication.date_validation if derniere_publication else None
    
    context = {
        'cours_publies': cours_list,
    }
    return render(request, 'grades/gestion_notes_publiees.html', context)


@login_required
@user_passes_test(can_manage_academique)
def remettre_notes_brouillon(request, cours_id):
    """
    Admin: Remettre toutes les notes publiées d'un cours en brouillon
    """
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "❌ Accès réservé aux administrateurs")
        return redirect('accounts:dashboard')
    
    cours = get_object_or_404(Cours, id=cours_id)
    
    # Récupérer uniquement les notes PUBLIÉES
    notes = Note.objects.filter(
        cours=cours,
        statut=STATUT_PUBLIEE  # Uniquement publiées
    ).select_related('etudiant__user')
    
    if not notes.exists():
        messages.error(request, "❌ Ce cours n'a pas de notes publiées.")
        return redirect('grades:gestion_notes_publiees')
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '').strip()
        
        # ✅ AUDIT: Remise en brouillon
        audit_action_generique(
            request, 
            'REMISE_BROUILLON', 
            f"Cours: {cours.code}",
            f"Notes publiées remises en brouillon. Nb: {notes.count()}. Motif: {motif[:50]}..."
        )
        
        # Mettre à jour toutes les notes publiées → brouillon
        updated_count=notes.update(
            statut=STATUT_BROUILLON,  # ou 'brouillon'
            date_validation=None,
            motif_rejet=None
        )
        
        messages.success(request, 
            f"✅ {updated_count} NOTE(S) REMISE(S) EN BROUILLON !\n"
            f"Les notes du cours '{cours.intitule}' ne sont plus visibles par les étudiants."
        )
        
        return redirect('grades:gestion_notes_publiees')
    
    context = {
        'cours': cours,
        'notes': notes,
        'notes_count': notes.count(),
    }
    return render(request, 'grades/confirmation_remettre_brouillon.html', context)

 
 
# # grades/views.py
# @login_required
# @user_passes_test(is_admin)
# def modifier_statut_note(request, note_id):
#     """
#     Admin: Modifier le statut d'une note (utilisé par le modal)
#     """
#     if request.user.role != User.Role.ADMIN:
#         messages.error(request, "❌ Accès réservé aux administrateurs")
#         return redirect('accounts:dashboard')
    
#     note = get_object_or_404(Note, id=note_id)
    
#     if request.method == 'POST':
#         nouveau_statut = request.POST.get('nouveau_statut')
#         motif = request.POST.get('motif', '').strip()
#         redirect_to = request.POST.get('redirect_to', 'grades:changer_statut_notes')
        
#         # Validation du workflow
#         transitions_autorisees = {
#             ('publiée', 'brouillon'): True,
#             ('soumise', 'publiée'): True,
#             ('soumise', 'rejetée'): True,
#             ('rejetée', 'brouillon'): True,
#         }
        
#         transition = (note.statut, nouveau_statut)
        
#         if transition in transitions_autorisees:
#             if nouveau_statut == 'rejetée' and not motif:
#                 messages.error(request, "❌ Motif requis pour rejeter une note")
#             else:
#                 # Appliquer le changement
#                 note.statut = nouveau_statut
                
#                 if nouveau_statut == 'publiée':
#                     note.date_validation = timezone.now()
#                     note.motif_rejet = None
#                 elif nouveau_statut == 'rejetée':
#                     note.motif_rejet = motif
#                 elif nouveau_statut == 'brouillon':
#                     note.date_validation = None
#                     if note.statut == 'rejetée':
#                         note.motif_rejet = None
                
#                 note.save()
                
#                 messages.success(request, 
#                     f"✅ Statut changé de '{note.get_statut_display()}' à '{dict(Note.STATUT_CHOICES)[nouveau_statut]}'"
#                 )
#         else:
#             messages.error(request, f"❌ Transition '{note.get_statut_display()}' → '{dict(Note.STATUT_CHOICES)[nouveau_statut]}' non autorisée")
    
#     return redirect(redirect_to)



# grades/views.py - VUE COMPLÈTE
@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def gestion_semestres(request):
    """
    Admin: Gestion des changements de semestres et promotions - UJEPH VERSION
    """
    from django.utils import timezone
    from .models import HistoriquePromotion
    
    # Statistiques
    stats = {
        's1': Etudiant.objects.filter(semestre_courant='S1', statut_academique='actif').count(),
        's2': Etudiant.objects.filter(semestre_courant='S2', statut_academique='actif').count(),
        'total': Etudiant.objects.filter(statut_academique='actif').count(),
    }
    
    annee_courante = f"{timezone.now().year}-{timezone.now().year+1}"
    
    # Historique récent (10 derniers)
    historique_recent = HistoriquePromotion.objects.select_related(
        'etudiant__user', 'effectue_par'
    ).order_by('-date_promotion')[:10]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'S1_to_S2':
            # Passage S1 → S2 (même niveau)
            etudiants = Etudiant.objects.filter(
                semestre_courant='S1', 
                statut_academique='actif'
            ).select_related('user')
            
            count = 0
            for etudiant in etudiants:
                # Sauvegarder l'historique
                HistoriquePromotion.objects.create(
                    etudiant=etudiant,
                    ancien_niveau=etudiant.niveau,
                    ancien_semestre='S1',
                    nouveau_niveau=etudiant.niveau,
                    nouveau_semestre='S2',
                    annee_academique=annee_courante,
                    decision='changement_semestre',
                    effectue_par=request.user,
                    notes=f"Passage S1 → S2 - Action groupée"
                )
                
                # Changer de semestre
                etudiant.semestre_courant = 'S2'
                etudiant.save()
                
                # Réattribuer les cours
                from .utils import reattribuer_cours_etudiant
                reattribuer_cours_etudiant(etudiant)
                
                count += 1
            
            messages.success(request, 
                f"✅ {count} étudiant(s) passé(s) de S1 à S2 avec succès !"
            )
            
        elif action == 'S2_to_S1':
            # GÉNÉRER LES RELEVÉS AUTOMATIQUEMENT APRÈS FIN D'ANNÉE
            # from .utils import generer_releve_notes
            
            # for etudiant in etudiants:
            #     # Générer relevé S2
            #     generer_releve_notes(etudiant, annee_courante, 'S2')
            
            # messages.info(request, 
            #    f"📄 Relevés S2 {annee_courante} générés automatiquement pour {etudiants.count()} étudiant(s)")
            #FIN POUR GENERER RELEVE...

            # Fin d'année : S2 → S1 avec promotion (UJEPH : 70/100)
            etudiants = Etudiant.objects.filter(
                semestre_courant='S2',
                statut_academique='actif'
            ).select_related('user', 'faculte')
            
            count_admis = 0
            count_redouble = 0
            
            for etudiant in etudiants:
                # 1. Calculer les moyennes
                from .utils import calculer_et_stocker_moyennes
                calculer_et_stocker_moyennes(etudiant)
                
                # 2. Décision basée sur la moyenne - UJEPH RÈGLE
                decision = None
                if etudiant.moyenne_generale:
                    if etudiant.moyenne_generale >= 70:  # ✅ UJEPH : 70/100
                        # Admis
                        decision = 'admis'
                        niveaux = ['1ere', '2e', '3e', '4e', '5e']
                        if etudiant.niveau in niveaux:
                            index = niveaux.index(etudiant.niveau)
                            if index < len(niveaux) - 1:
                                # Passage au niveau supérieur
                                etudiant.niveau = niveaux[index + 1]
                                count_admis += 1
                            else:
                                # Dernier niveau : diplômé
                                etudiant.statut_academique = 'diplome'
                                decision = 'diplome'
                                count_admis += 1
                    else:  # < 70/100
                        # Redouble
                        decision = 'redouble'
                        etudiant.statut_academique = 'redoublant'
                        count_redouble += 1
                else:
                    # Pas de moyenne → redouble par défaut
                    decision = 'redouble'
                    etudiant.statut_academique = 'redoublant'
                    count_redouble += 1
                
                # 3. Changer de semestre (S2 → S1 pour tous)
                ancien_semestre = etudiant.semestre_courant
                etudiant.semestre_courant = 'S1'
                etudiant.save()
                
                # 4. Sauvegarder l'historique
                HistoriquePromotion.objects.create(
                    etudiant=etudiant,
                    ancien_niveau=etudiant.niveau,
                    ancien_semestre=ancien_semestre,
                    nouveau_niveau=etudiant.niveau,
                    nouveau_semestre='S1',
                    annee_academique=annee_courante,
                    decision=decision,
                    moyenne_generale=etudiant.moyenne_generale,
                    effectue_par=request.user,
                    notes=f"Moyenne: {etudiant.moyenne_generale or 0}/100"
                )
                
                # 5. Réattribuer les cours
                from .utils import reattribuer_cours_etudiant
                reattribuer_cours_etudiant(etudiant)
            
            # Message de succès détaillé
            message_parts = [f"✅ Fin d'année académique terminée !"]
            if count_admis > 0:
                message_parts.append(f"{count_admis} admis")
            if count_redouble > 0:
                message_parts.append(f"{count_redouble} redoublements")
            
            messages.success(request, " | ".join(message_parts))
        
        return redirect('grades:gestion_semestres')
    
    context = {
        'stats': stats,
        'annee_courante': annee_courante,
        'historique_recent': historique_recent,
    }
    
    return render(request, 'grades/gestion_semestres.html', context)


# grades/views.py - AJOUTER cette vue simple
# @login_required
# @user_passes_test(is_admin)
# def gestion_semestres(request):
#     """
#     Interface simple pour changer les semestres
#     """
#     stats = {
#         's1': Etudiant.objects.filter(semestre_courant='S1', statut_academique='actif').count(),
#         's2': Etudiant.objects.filter(semestre_courant='S2', statut_academique='actif').count(),
#     }
    
#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         if action == 'S1_to_S2':
#             # Simple changement S1 → S2
#             etudiants = Etudiant.objects.filter(semestre_courant='S1', statut_academique='actif')
#             for etudiant in etudiants:
#                 etudiant.semestre_courant = 'S2'
#                 etudiant.save()
#                 reattribuer_cours_etudiant(etudiant)  # Réattribue les cours S2
            
#             messages.success(request, f"✅ {etudiants.count()} étudiants passés de S1 à S2")
            
#         elif action == 'S2_to_S1':
#             # Fin d'année : S2 → S1 avec promotion
#             etudiants = Etudiant.objects.filter(semestre_courant='S2', statut_academique='actif')
            
#             for etudiant in etudiants:
#                 # 1. Calculer les moyennes
#                 calculer_et_stocker_moyennes(etudiant)
                
#                 # 2. Décision de promotion basée sur moyenne
#                 if etudiant.moyenne_generale and etudiant.moyenne_generale >= 10:
#                     # Admis : passer au niveau suivant
#                     niveaux = ['1ere', '2e', '3e', '4e', '5e']
#                     if etudiant.niveau in niveaux:
#                         index = niveaux.index(etudiant.niveau)
#                         if index < len(niveaux) - 1:
#                             etudiant.niveau = niveaux[index + 1]
#                             decision = 'admis'
#                         else:
#                             etudiant.statut_academique = 'diplome'
#                             decision = 'diplome'
#                 else:
#                     # Redouble ou passage conditionnel
#                     decision = 'redouble' if etudiant.moyenne_generale and etudiant.moyenne_generale < 7 else 'passage_conditionnel'
                
#                 # 3. Changer de semestre
#                 etudiant.semestre_courant = 'S1'
#                 etudiant.save()
                
#                 # 4. Historique
#                 HistoriquePromotion.objects.create(
#                     etudiant=etudiant,
#                     ancien_niveau=etudiant.niveau,
#                     ancien_semestre='S2',
#                     nouveau_niveau=etudiant.niveau,
#                     nouveau_semestre='S1',
#                     annee_academique=etudiant.annee_academique_courante,
#                     decision=decision,
#                     moyenne_generale=etudiant.moyenne_generale,
#                     effectue_par=request.user
#                 )
                
#                 # 5. Réattribuer les cours
#                 reattribuer_cours_etudiant(etudiant)
            
#             messages.success(request, f"✅ {etudiants.count()} étudiants passés de S2 à S1 avec promotions")
        
#         return redirect('grades:gestion_semestres')
    
#     context = {'stats': stats}
#     return render(request, 'grades/gestion_semestres.html', context)


#SECTION POUR LES RELEVEES DE NOTES
# grades/views.py - AJOUTEZ CES VUES

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def generer_releves_semestre(request):
    """
    Admin: Génère les relevés pour tous les étudiants d'un semestre
    """
    if request.method == 'POST':
        semestre = request.POST.get('semestre')
        annee_academique = request.POST.get('annee_academique')
        
        if not semestre or not annee_academique:
            messages.error(request, "❌ Veuillez spécifier le semestre et l'année académique")
            return redirect('grades:gestion_releves')
        
        # Filtrer les étudiants actifs
        etudiants = Etudiant.objects.filter(
            statut_academique='actif'
        ).select_related('user', 'faculte')
        
        total_generes = 0
        erreurs = []
        
        for etudiant in etudiants:
            try:
                from .utils import generer_releve_notes
                generer_releve_notes(etudiant, annee_academique, semestre)
                total_generes += 1
            except Exception as e:
                erreurs.append(f"{etudiant.matricule}: {str(e)}")
        
        if total_generes > 0:
            messages.success(request, 
                f"✅ {total_generes} relevé(s) généré(s) pour {semestre} {annee_academique}"
            )
        
        if erreurs:
            messages.warning(request, 
                f"⚠️ {len(erreurs)} erreur(s) lors de la génération"
            )
        
        return redirect('grades:gestion_releves')
    
    # GET: Afficher le formulaire
    from django.utils import timezone
    annee_courante = f"{timezone.now().year}-{timezone.now().year+1}"
    
    context = {
        'annee_courante': annee_courante,
        'semestres': [('S1', 'Semestre 1'), ('S2', 'Semestre 2')],
    }
    
    return render(request, 'grades/generer_releves.html', context)

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def gestion_releves(request):
    """
    Admin: Liste et gestion des relevés de notes
    """
    # Filtres
    annee = request.GET.get('annee', '')
    semestre = request.GET.get('semestre', '')
    faculte_id = request.GET.get('faculte', '')
    etudiant_search = request.GET.get('etudiant', '')
    
    releves = ReleveDeNotes.objects.select_related(
        'etudiant__user', 
        'etudiant__faculte',
        'faculte'
    ).all()
    
    # Appliquer les filtres
    if annee:
        releves = releves.filter(annee_academique=annee)
    
    if semestre:
        releves = releves.filter(semestre=semestre)
    
    if faculte_id:
        releves = releves.filter(etudiant__faculte_id=faculte_id)
    
    if etudiant_search:
        releves = releves.filter(
            Q(etudiant__matricule__icontains=etudiant_search) |
            Q(etudiant__user__last_name__icontains=etudiant_search) |
            Q(etudiant__user__first_name__icontains=etudiant_search)
        )
    
    # Pagination
    paginator = Paginator(releves.order_by('-annee_academique', 'semestre', 'etudiant__matricule'), 20)
    page = request.GET.get('page')
    releves_page = paginator.get_page(page)
    
    # Liste des années disponibles
    annees_disponibles = ReleveDeNotes.objects.values_list(
        'annee_academique', flat=True
    ).distinct().order_by('-annee_academique')
    
    # Liste des facultés
    from academics.models import Faculte
    facultes = Faculte.objects.all()
    
    context = {
        'releves': releves_page,
        'annees_disponibles': annees_disponibles,
        'facultes': facultes,
        'filters': {
            'annee': annee,
            'semestre': semestre,
            'faculte': faculte_id,
            'etudiant': etudiant_search,
        },
    }
    
    return render(request, 'grades/gestion_releves.html', context)

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def gestion_releves_complete(request):
    """
    Admin: Gestion complète des relevés de notes
    """
    # Récupérer les paramètres de filtrage
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    moyenne_min = request.GET.get('moyenne_min', '')
    annee = request.GET.get('annee', '')
    semestre = request.GET.get('semestre', '')
    faculte_id = request.GET.get('faculte', '')
    niveau = request.GET.get('niveau', '')
    
    # Base queryset - adapté à votre modèle
    releves = ReleveDeNotes.objects.select_related(
        'etudiant__user', 
        'etudiant__faculte',
        'faculte'
    ).all()
    
    # Appliquer les filtres
    if annee:
        releves = releves.filter(annee_academique=annee)
    
    if semestre:
        releves = releves.filter(semestre=semestre)
    
    if faculte_id:
        releves = releves.filter(etudiant__faculte_id=faculte_id)
    
    if niveau:
        releves = releves.filter(etudiant__niveau=niveau)
    
    if statut:
        releves = releves.filter(statut=statut)
    
    if moyenne_min:
        try:
            releves = releves.filter(moyenne_semestre__gte=float(moyenne_min))
        except ValueError:
            pass
    
    if search:
        releves = releves.filter(
            Q(etudiant__matricule__icontains=search) |
            Q(etudiant__user__last_name__icontains=search) |
            Q(etudiant__user__first_name__icontains=search)
        )
    
    # Calculer les statistiques
    total_releves = releves.count()
    
    # Pagination
    paginator = Paginator(releves.order_by('-annee_academique', '-semestre', 'etudiant__matricule'), 25)
    page = request.GET.get('page')
    releves_page = paginator.get_page(page)
    
    # Données pour les filtres
    annees_disponibles = ReleveDeNotes.objects.values_list(
        'annee_academique', flat=True
    ).distinct().order_by('-annee_academique')
    
    from academics.models import Faculte
    from django.db.models import Count, Avg
    
    facultes = Faculte.objects.all()
    
    # Calculer des statistiques
    stats = {
        'total_releves': ReleveDeNotes.objects.count(),
        'releves_valides': ReleveDeNotes.objects.filter(statut='VALIDE').count(),
        'releves_brouillon': ReleveDeNotes.objects.filter(statut='BROUILLON').count(),
        'moyenne_generale': ReleveDeNotes.objects.filter(statut='VALIDE')
                                .aggregate(avg=Avg('moyenne_semestre'))['avg'] or 0,
        'etudiants_couverts': ReleveDeNotes.objects.values('etudiant').distinct().count(),
        'taux_reussite': 75,  # À calculer selon votre logique
        'annee_actuelle': "2024-2025",
        'semestre_actif': "S1",
    }
    
    context = {
        'releves': releves_page,
        'stats': stats,
        'annees_disponibles': annees_disponibles,
        'facultes': facultes,
        # Utiliser les choix de niveau de votre modèle Etudiant
        'niveaux': Etudiant.NIVEAU_CHOICES,
        'filters': {
            'search': search,
            'statut': statut,
            'moyenne_min': moyenne_min,
            'annee': annee,
            'semestre': semestre,
            'faculte': faculte_id,
            'niveau': niveau,
        },
    }
    
    return render(request, 'grades/gestion_releves_complete.html', context)

@login_required
def consulter_releve_etudiant(request, releve_id=None):
    """
    Étudiant/Admin: Consulter un relevé spécifique
    """
    if releve_id:
        # Vue détaillée d'un relevé spécifique
        releve = get_object_or_404(ReleveDeNotes, id=releve_id)
        
        # Vérification des permissions
        if request.user.role == User.Role.ETUDIANT:
            if not hasattr(request.user, 'etudiant') or releve.etudiant != request.user.etudiant:
                messages.error(request, "❌ Accès non autorisé à ce relevé")
                return redirect('grades:mes_releves')
        
        # Calculer les statistiques
        stats = releve.calculer_stats()
        
        context = {
            'releve': releve,
            'stats': stats,
            'notes_details': releve.details_notes.get('notes', []),
        }
        
        return render(request, 'grades/detail_releve.html', context)
    
    else:
        # Liste des relevés pour l'étudiant connecté
        if request.user.role != User.Role.ETUDIANT or not hasattr(request.user, 'etudiant'):
            messages.error(request, "❌ Accès réservé aux étudiants")
            return redirect('accounts:dashboard')
        
        etudiant = request.user.etudiant
        releves = ReleveDeNotes.objects.filter(
            etudiant=etudiant
        ).order_by('-annee_academique', 'semestre')
        
        # Grouper par année
        releves_par_annee = {}
        for releve in releves:
            if releve.annee_academique not in releves_par_annee:
                releves_par_annee[releve.annee_academique] = []
            releves_par_annee[releve.annee_academique].append(releve)
        
        context = {
            'etudiant': etudiant,
            'releves_par_annee': releves_par_annee,
        }
        
        return render(request, 'grades/mes_releves.html', context)

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def releve_par_cours(request, cours_id):
    """
    Admin/Professeur: Relevé des notes pour un cours spécifique
    """
    cours = get_object_or_404(Cours, id=cours_id)
    
    # Vérification des permissions pour les professeurs
    if request.user.role == User.Role.PROFESSEUR and cours.professeur != request.user:
        messages.error(request, "❌ Accès non autorisé à ce cours")
        return redirect('academics:mes_cours_professeur')
    
    # Récupérer les notes publiées pour ce cours
    notes = Note.objects.filter(
        cours=cours,
        statut='publiée'
    ).select_related(
        'etudiant__user',
        'etudiant__faculte'
    ).order_by('etudiant__user__last_name', 'etudiant__user__first_name')
    
    # Statistiques du cours
    stats = {
        'total_etudiants': notes.count(),
        'moyenne_cours': round(sum(n.valeur for n in notes) / notes.count(), 2) if notes.count() > 0 else 0,
        'note_max': max(n.valeur for n in notes) if notes.count() > 0 else 0,
        'note_min': min(n.valeur for n in notes) if notes.count() > 0 else 0,
        'valides_70': sum(1 for n in notes if n.valeur >= 70),
        'echecs_70': sum(1 for n in notes if n.valeur < 70),
    }
    
    context = {
        'cours': cours,
        'notes': notes,
        'stats': stats,
    }
    
    return render(request, 'grades/releve_par_cours.html', context)

@login_required
@permission_required(can_access_academique, redirect_url='accounts:dashboard')
def exporter_releve_csv(request, releve_id):
    """
    Exporte un relevé au format CSV
    """
    releve = get_object_or_404(ReleveDeNotes, id=releve_id)
    notes = releve.details_notes.get('notes', [])
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="releve_{releve.etudiant.matricule}_{releve.annee_academique}_{releve.semestre}.csv"'
    
    writer = csv.writer(response)
    
    # En-tête
    writer.writerow(['RELEVÉ DE NOTES - UJEPH'])
    writer.writerow([f'Étudiant: {releve.etudiant.user.get_full_name()}'])
    writer.writerow([f'Matricule: {releve.etudiant.matricule}'])
    writer.writerow([f'Année académique: {releve.annee_academique} - Semestre: {releve.semestre}'])
    writer.writerow([f'Niveau: {releve.niveau} - Faculté: {releve.faculte.nom if releve.faculte else "N/A"}'])
    writer.writerow([''])  # Ligne vide
    
    # Détails des notes
    writer.writerow(['Code', 'Cours', 'Note/100', 'Crédits', 'Professeur'])
    writer.writerow(['-----', '-----', '--------', '-------', '----------'])
    
    for note in notes:
        writer.writerow([
            note['cours_code'],
            note['cours_intitule'],
            note['note'],
            note['credits'],
            note['professeur']
        ])
    
    writer.writerow([''])  # Ligne vide
    
    # Résumé
    stats = releve.calculer_stats()
    if stats:
        writer.writerow(['RÉSUMÉ'])
        writer.writerow([f'Moyenne semestre: {releve.moyenne_semestre:.2f}/100'])
        if releve.moyenne_cumulee:
            writer.writerow([f'Moyenne cumulée: {releve.moyenne_cumulee:.2f}/100'])
        writer.writerow([f'Nombre de cours: {stats["nb_cours"]}'])
        writer.writerow([f'Cours validés (≥70): {stats["cours_valides"]}'])
        writer.writerow([f'Cours échoués (<70): {stats["cours_echoues"]}'])
    
    writer.writerow([''])  # Ligne vide
    writer.writerow([f'Date de génération: {timezone.now().strftime("%d/%m/%Y %H:%M")}'])
    
    return response

@login_required
def historique_complet_etudiant(request, etudiant_id=None):
    """
    Affiche l'historique complet d'un étudiant (admin) ou du propre étudiant
    """
    if etudiant_id and request.user.role == User.Role.ADMIN:
        # Admin: consulter un étudiant spécifique
        etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    elif request.user.role == User.Role.ETUDIANT and hasattr(request.user, 'etudiant'):
        # Étudiant: consulter son propre historique
        etudiant = request.user.etudiant
    else:
        messages.error(request, "❌ Accès non autorisé")
        return redirect('accounts:dashboard')
    
    # Récupérer tous les relevés
    releves = ReleveDeNotes.objects.filter(
        etudiant=etudiant
    ).order_by('annee_academique', 'semestre')
    
    # Récupérer l'historique des promotions
    historique = HistoriquePromotion.objects.filter(
        etudiant=etudiant
    ).order_by('annee_academique', 'date_promotion')
    
    # Calculer l'évolution de la moyenne
    evolution = []
    for releve in releves:
        evolution.append({
            'periode': f"{releve.annee_academique} {releve.semestre}",
            'moyenne': float(releve.moyenne_semestre),
            'niveau': releve.niveau,
        })
    
    context = {
        'etudiant': etudiant,
        'releves': releves,
        'historique': historique,
        'evolution': evolution,
    }
    
    return render(request, 'grades/historique_complet.html', context)

from django.http import JsonResponse
from django.db.models import Count, Q

@login_required
@permission_required(can_access_academique)
def api_stats_releves(request):
    """API pour les statistiques de génération de relevés"""
    annee = request.GET.get('annee')
    semestre = request.GET.get('semestre')
    
    if not annee or not semestre:
        return JsonResponse({'error': 'Paramètres manquants'}, status=400)
    
    # Calculer les statistiques
    etudiants_actifs = Etudiant.objects.filter(
        statut_academique='actif'
    ).count()
    
    notes_publiees = Note.objects.filter(
        cours__semestre=semestre,
        statut='publiée'
    ).count()
    
    releves_existants = ReleveDeNotes.objects.filter(
        annee_academique=annee,
        semestre=semestre
    ).count()
    
    return JsonResponse({
        'etudiants_actifs': etudiants_actifs,
        'notes_publiees': notes_publiees,
        'releves_existants': releves_existants,
    })

@login_required
@permission_required(can_access_academique)
def api_simulation_releves(request):
    """API pour la simulation de génération"""
    annee = request.GET.get('annee')
    semestre = request.GET.get('semestre')
    
    # Simulation
    etudiants_concernes = Etudiant.objects.filter(
        statut_academique='actif'
    ).count()
    
    notes_a_inclure = Note.objects.filter(
        cours__semestre=semestre,
        statut='publiée',
        annee_academique=annee
    ).count()
    
    # Compter les relevés existants
    releves_existants = ReleveDeNotes.objects.filter(
        annee_academique=annee,
        semestre=semestre
    ).count()
    
    # Éstimation des nouveaux relevés
    etudiants_avec_notes = Etudiant.objects.filter(
        statut_academique='actif',
        note__cours__semestre=semestre,
        note__statut='publiée',
        note__annee_academique=annee
    ).distinct().count()
    
    nouveaux_releves = max(0, etudiants_avec_notes - releves_existants)
    
    return JsonResponse({
        'etudiants_concernes': etudiants_concernes,
        'notes_a_inclure': notes_a_inclure,
        'releves_a_mettre_a_jour': releves_existants,
        'nouveaux_releves': nouveaux_releves,
    })

