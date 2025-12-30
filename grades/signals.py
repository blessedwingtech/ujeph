# signals.py - CORRIGÉ pour votre structure
from django.db.models.signals import post_save
from django.dispatch import receiver
from academics.models import Cours
from accounts.models import Etudiant
from grades.models import InscriptionCours, Note


# Signal 1: Quand un étudiant est créé/modifié - CORRIGÉ
@receiver(post_save, sender=Etudiant)
def subscribe_student_to_relevant_courses(sender, instance, created, **kwargs):
    """
    Inscrit automatiquement un étudiant à tous les cours qui correspondent
    à ses critères (faculté, niveau, semestre)
    """
    if created:
        # Pour une création, inscrire aux cours existants correspondants
        # MAINTENANT: semestre_courant (Etudiant) et semestre (Cours) sont tous deux des CharField
        cours_concernes = Cours.objects.filter(
            faculte=instance.faculte,
            niveau=instance.niveau,
            semestre=instance.semestre_courant  # ← DIRECT COMPARISON NOW
        )
        
        print(f"🎓 Nouvel étudiant {instance} - Recherche cours pour:")
        print(f"   Faculté: {instance.faculte}")
        print(f"   Niveau: {instance.niveau}")
        print(f"   Semestre: {instance.semestre_courant}")
        print(f"   Cours trouvés: {cours_concernes.count()}")
        
        inscriptions_crees = 0
        for cours in cours_concernes:
            _, created = InscriptionCours.objects.get_or_create(
                etudiant=instance,
                cours=cours
            )
            if created:
                inscriptions_crees += 1
                print(f"   ➕ Inscrit au cours: {cours}")
        
        print(f"✅ Total inscriptions créées: {inscriptions_crees}")
    
    elif not created:
        # Pour une modification, vérifier si les champs critiques ont changé
        try:
            ancien_etudiant = Etudiant.objects.get(id=instance.id)
            
            # Vérifier si faculte, niveau ou semestre_courant ont changé
            criteres_modifies = (
                ancien_etudiant.faculte != instance.faculte or 
                ancien_etudiant.niveau != instance.niveau or 
                ancien_etudiant.semestre_courant != instance.semestre_courant
            )
            
            if criteres_modifies:
                print(f"🔄 Modifications détectées pour {instance}:")
                print(f"   Ancien: Fac={ancien_etudiant.faculte}, Niv={ancien_etudiant.niveau}, Sem={ancien_etudiant.semestre_courant}")
                print(f"   Nouveau: Fac={instance.faculte}, Niv={instance.niveau}, Sem={instance.semestre_courant}")
                
                # 1. Désinscrire des anciens cours
                anciens_cours = Cours.objects.filter(
                    faculte=ancien_etudiant.faculte,
                    niveau=ancien_etudiant.niveau,
                    semestre=ancien_etudiant.semestre_courant
                )
                
                supprimees, _ = InscriptionCours.objects.filter(
                    etudiant=instance,
                    cours__in=anciens_cours
                ).delete()
                
                print(f"   🗑️ Inscriptions supprimées: {supprimees}")
                
                # 2. Inscrire aux nouveaux cours
                nouveaux_cours = Cours.objects.filter(
                    faculte=instance.faculte,
                    niveau=instance.niveau,
                    semestre=instance.semestre_courant
                )
                
                inscriptions_crees = 0
                for cours in nouveaux_cours:
                    _, created = InscriptionCours.objects.get_or_create(
                        etudiant=instance,
                        cours=cours
                    )
                    if created:
                        inscriptions_crees += 1
                
                print(f"   ➕ Nouvelles inscriptions: {inscriptions_crees}")
                print(f"✅ {instance} réinscrit après modification")
                
        except Etudiant.DoesNotExist:
            pass


# Signal 2: Quand un cours est créé - CORRIGÉ
@receiver(post_save, sender=Cours)
def subscribe_existing_students_to_new_course(sender, instance, created, **kwargs):
    """
    Lorsqu'un nouveau cours est créé, inscrire automatiquement 
    tous les étudiants existants qui correspondent aux critères du cours
    """
    if created:
        print(f"🎯 NOUVEAU COURS CRÉÉ: {instance.code} - {instance.intitule}")
        print(f"   Critères: Fac={instance.faculte}, Niv={instance.niveau}, Sem={instance.semestre}")
        
        # Rechercher les étudiants correspondants
        etudiants_concernes = Etudiant.objects.filter(
            faculte=instance.faculte,
            niveau=instance.niveau,
            semestre_courant=instance.semestre  # ← COMPARAISON DIRECTE
        )
        
        print(f"   📊 Étudiants correspondants trouvés: {etudiants_concernes.count()}")
        
        inscriptions_crees = 0
        for etudiant in etudiants_concernes:
            # Vérifier si l'inscription existe déjà
            if not InscriptionCours.objects.filter(
                etudiant=etudiant,
                cours=instance
            ).exists():
                InscriptionCours.objects.create(
                    etudiant=etudiant,
                    cours=instance
                )
                inscriptions_crees += 1
                print(f"   ➕ {etudiant.matricule} inscrit au cours")
        
        if inscriptions_crees > 0:
            print(f"✅ {inscriptions_crees} inscription(s) créée(s) pour {instance.code}")
        else:
            print(f"ℹ️ Aucune nouvelle inscription nécessaire")


# Signal 3: Sécurité pour les notes
@receiver(post_save, sender=Note)
def create_inscription_on_note_creation(sender, instance, created, **kwargs):
    """
    Crée automatiquement une inscription quand une note est créée
    pour un étudiant qui n'est pas encore inscrit au cours
    """
    if created:
        # Vérifier si l'inscription existe déjà
        if not InscriptionCours.objects.filter(
            etudiant=instance.etudiant,
            cours=instance.cours
        ).exists():
            
            # Créer l'inscription manquante
            InscriptionCours.objects.create(
                etudiant=instance.etudiant,
                cours=instance.cours
            )
            print(f"⚠️ Inscription créée pour {instance.etudiant} au cours {instance.cours} suite à une note")
            