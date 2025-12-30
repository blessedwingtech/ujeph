STATUT_BROUILLON = 'brouillon'
STATUT_SOUMISE = 'soumise'
STATUT_PUBLIEE = 'publiée'
STATUT_REJETEE = 'rejetée'

STATUTS_MODIFIABLES = [STATUT_BROUILLON, STATUT_REJETEE]

# grades/utils.py - CRÉER ce fichier
from academics.models import Cours
from grades.models import InscriptionCours
from django.utils import timezone

def reattribuer_cours_etudiant(etudiant):
    """
    Réattribue les cours à un étudiant selon son niveau/semestre
    UTILISE VOS MODÈLES EXISTANTS SANS LES MODIFIER
    """
    try:
        print(f"📚 Réattribution cours pour {etudiant.matricule}")
        
        # 1. Supprimer les anciennes inscriptions (VOTRE MODÈLE EXISTANT)
        supprimes = InscriptionCours.objects.filter(etudiant=etudiant).delete()
        print(f"   🗑️ {supprimes[0]} anciens cours supprimés")
        
        # 2. Trouver les nouveaux cours (VOTRE MODÈLE EXISTANT)
        nouveaux_cours = Cours.objects.filter(
            faculte=etudiant.faculte,
            niveau=etudiant.niveau,
            semestre=etudiant.semestre_courant
        )
        
        # 3. Créer les nouvelles inscriptions (VOTRE MODÈLE EXISTANT)
        for cours in nouveaux_cours:
            InscriptionCours.objects.get_or_create(
                etudiant=etudiant,
                cours=cours
            )
        
        print(f"   ✅ {nouveaux_cours.count()} nouveaux cours attribués")
        return True
        
    except Exception as e:
        print(f"❌ Erreur réattribution: {e}")
        return False


def calculer_et_stocker_moyennes(etudiant):
    """
    Calcule et stocke les moyennes d'un étudiant
    UTILISE VOS MODÈLES EXISTANTS
    """
    from grades.models import Note, MoyenneSemestre
    
    annee_courante = f"{timezone.now().year}-{timezone.now().year+1}"
    
    # Pour chaque semestre
    for semestre in ['S1', 'S2']:
        notes = Note.objects.filter(
            etudiant=etudiant,
            cours__semestre=semestre,
            statut='publiée'
        )
        
        if notes.exists():
            total = sum(float(note.valeur) for note in notes)
            moyenne = round(total / notes.count(), 2)
            
            # Stocker dans MoyenneSemestre (VOTRE MODÈLE EXISTANT)
            MoyenneSemestre.objects.update_or_create(
                etudiant=etudiant,
                semestre=semestre,
                annee_academique=annee_courante,
                defaults={'moyenne': moyenne}
            )
            
            print(f"   📊 {semestre}: {moyenne}/100 ({notes.count()} notes)")
    
    # Calculer et stocker la moyenne générale
    moyenne_gen = etudiant.calculer_moyenne_generale()
    if moyenne_gen:
        etudiant.moyenne_generale = round(moyenne_gen, 2)
        etudiant.save()
        print(f"   🎯 Moyenne générale: {etudiant.moyenne_generale}/100")



#SECTION POUR RELEVEE DE NOTES
# grades/utils.py - CRÉEZ CE FICHIER

from django.utils import timezone
from django.db import transaction
import json

def generer_releve_notes(etudiant, annee_academique, semestre):
    """
    Génère et archive un relevé de notes pour un étudiant donné
    """
    from .models import Note, ReleveDeNotes, InscriptionCours
    
    # Récupérer toutes les notes publiées pour ce semestre
    notes = Note.objects.filter(
        etudiant=etudiant,
        cours__semestre=semestre,
        statut='publiée',
        annee_academique=annee_academique
    ).select_related('cours', 'cours__faculte')
    
    # Structure JSON des détails
    details = {
        'etudiant': {
            'matricule': etudiant.matricule,
            'nom_complet': etudiant.user.get_full_name(),
            'niveau': etudiant.niveau,
            'faculte': etudiant.faculte.nom,
        },
        'annee_academique': annee_academique,
        'semestre': semestre,
        'date_generation': timezone.now().isoformat(),
        'notes': []
    }
    
    total_points = 0
    total_coefficients = 0
    
    for note in notes:
        note_data = {
            'cours_code': note.cours.code,
            'cours_intitule': note.cours.intitule,
            'note': float(note.valeur),
            'coefficient': 1,  # À adapter si vous avez des coefficients
            'credits': note.cours.credits,
            'professeur': note.cours.professeur.get_full_name() if note.cours.professeur else '',
            'date_publication': note.date_validation.isoformat() if note.date_validation else None,
        }
        
        details['notes'].append(note_data)
        total_points += float(note.valeur)
        total_coefficients += 1
    
    # Calculer la moyenne
    moyenne_semestre = round(total_points / total_coefficients, 2) if total_coefficients > 0 else 0
    
    # Créer ou mettre à jour le relevé
    with transaction.atomic():
        releve, created = ReleveDeNotes.objects.update_or_create(
            etudiant=etudiant,
            annee_academique=annee_academique,
            semestre=semestre,
            defaults={
                'niveau': etudiant.niveau,
                'faculte': etudiant.faculte,
                'moyenne_semestre': moyenne_semestre,
                'details_notes': details,
                'statut': etudiant.statut_academique,
                'valide_par': None,  # À remplir lors de la validation
            }
        )
        
        # Mettre à jour la moyenne cumulée si S2
        if semestre == 'S2':
            update_moyenne_cumulee(etudiant, annee_academique)
    
    return releve

def update_moyenne_cumulee(etudiant, annee_academique):
    """Calcule et met à jour la moyenne cumulée pour l'année"""
    from .models import ReleveDeNotes, MoyenneSemestre
    
    # Récupérer les relevés S1 et S2
    releve_s1 = ReleveDeNotes.objects.filter(
        etudiant=etudiant,
        annee_academique=annee_academique,
        semestre='S1'
    ).first()
    
    releve_s2 = ReleveDeNotes.objects.filter(
        etudiant=etudiant,
        annee_academique=annee_academique,
        semestre='S2'
    ).first()
    
    if releve_s1 and releve_s2:
        moyenne_cumulee = (releve_s1.moyenne_semestre + releve_s2.moyenne_semestre) / 2
        
        # Mettre à jour les deux relevés
        ReleveDeNotes.objects.filter(
            etudiant=etudiant,
            annee_academique=annee_academique
        ).update(moyenne_cumulee=moyenne_cumulee)
        
        # Mettre à jour aussi dans MoyenneSemestre
        moyenne_s1 = MoyenneSemestre.objects.filter(
            etudiant=etudiant,
            semestre='S1',
            annee_academique=annee_academique
        ).first()
        
        moyenne_s2 = MoyenneSemestre.objects.filter(
            etudiant=etudiant,
            semestre='S2',
            annee_academique=annee_academique
        ).first()
        
        if moyenne_s1:
            moyenne_s1.moyenne = releve_s1.moyenne_semestre
            moyenne_s1.save()
        
        if moyenne_s2:
            moyenne_s2.moyenne = releve_s2.moyenne_semestre
            moyenne_s2.save()       
