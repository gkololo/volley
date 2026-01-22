#!/usr/bin/env python3
"""
Script de migration : Declaration.date_tournoi → Tournoi

Ce script :
1. Trouve toutes les combinaisons uniques (date, categorie, sexe, zone) dans Declaration
2. Crée un objet Tournoi pour chaque combinaison
3. Lie chaque Declaration à son Tournoi correspondant

Usage:
    python3 migrate_data_to_tournois.py
"""

import os
import sys
import django
from pathlib import Path
from collections import defaultdict

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

# ⚠️ IMPORTANT : Importer les modèles APRÈS django.setup()
from django.db import transaction
from saisie_equipes.models import Declaration, Tournoi, StatutTournoi

def analyser_declarations():
    """Analyse les déclarations existantes"""
    print("\n" + "="*60)
    print("📊 ANALYSE DES DÉCLARATIONS EXISTANTES")
    print("="*60)
    
    declarations = Declaration.objects.all()
    total = declarations.count()
    
    print(f"\n📈 Total de déclarations : {total}")
    
    if total == 0:
        print("\n⚠️  Aucune déclaration à migrer !")
        return None
    
    # Grouper par (date, categorie, sexe, zone)
    groupes = defaultdict(list)
    
    for decl in declarations:
        cle = (
            decl.date_tournoi,
            decl.categorie_age,
            decl.sexe,
            decl.zone or ''  # Convertir None en ''
        )
        groupes[cle].append(decl)
    
    print(f"\n🎯 Combinaisons uniques trouvées : {len(groupes)}")
    print("\nDétails :")
    print("-" * 60)
    
    for i, (cle, declarations_groupe) in enumerate(sorted(groupes.items()), 1):
        date, cat, sexe, zone = cle
        nb_decls = len(declarations_groupe)
        nb_equipes = sum(d.nombre_equipes for d in declarations_groupe)
        zone_str = f" - Zone {zone}" if zone else ""
        
        print(f"{i:2d}. {date.strftime('%d/%m/%Y')} | "
              f"{cat} {sexe}{zone_str:15s} → "
              f"{nb_decls:2d} clubs, {nb_equipes:3d} équipes")
    
    return groupes

def creer_tournois(groupes):
    """Crée les tournois à partir des groupes"""
    print("\n" + "="*60)
    print("🏗️  CRÉATION DES TOURNOIS")
    print("="*60)
    
    tournois_crees = []
    
    for i, (cle, declarations_groupe) in enumerate(sorted(groupes.items()), 1):
        date, cat, sexe, zone = cle
        
        # Vérifier si le tournoi existe déjà
        tournoi_existant = Tournoi.objects.filter(
            date=date,
            categorie_age=cat,
            sexe=sexe,
            zone=zone
        ).first()
        
        if tournoi_existant:
            print(f"ℹ️  {i:2d}. Tournoi existe déjà : {tournoi_existant}")
            tournois_crees.append((cle, tournoi_existant))
            continue
        
        # Créer le nouveau tournoi
        tournoi = Tournoi(
            date=date,
            categorie_age=cat,
            sexe=sexe,
            zone=zone,
            statut=StatutTournoi.PLANIFIE,
            est_publie=True
        )
        tournoi.save()
        
        print(f"✅ {i:2d}. Tournoi créé : {tournoi}")
        tournois_crees.append((cle, tournoi))
    
    return dict(tournois_crees)

def lier_declarations_aux_tournois(groupes, tournois_map):
    """Lie chaque déclaration à son tournoi"""
    print("\n" + "="*60)
    print("🔗 LIAISON DECLARATIONS ↔ TOURNOIS")
    print("="*60)
    
    total_liees = 0
    erreurs = []
    
    for cle, declarations_groupe in groupes.items():
        tournoi = tournois_map.get(cle)
        
        if not tournoi:
            erreurs.append(f"❌ Pas de tournoi trouvé pour {cle}")
            continue
        
        for decl in declarations_groupe:
            if decl.tournoi is not None:
                print(f"⚠️  Déclaration {decl.id} déjà liée à un tournoi")
                continue
            
            decl.tournoi = tournoi
            decl.save(update_fields=['tournoi'])
            total_liees += 1
    
    print(f"\n✅ {total_liees} déclarations liées avec succès")
    
    if erreurs:
        print("\n❌ ERREURS :")
        for erreur in erreurs:
            print(f"   {erreur}")
    
    return total_liees, len(erreurs)

def verifier_coherence():
    """Vérifie que toutes les déclarations sont bien liées"""
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DE LA COHÉRENCE")
    print("="*60)
    
    total_declarations = Declaration.objects.count()
    declarations_liees = Declaration.objects.filter(tournoi__isnull=False).count()
    declarations_orphelines = Declaration.objects.filter(tournoi__isnull=True).count()
    
    print(f"\n📊 Déclarations totales    : {total_declarations}")
    print(f"✅ Déclarations liées      : {declarations_liees}")
    print(f"⚠️  Déclarations orphelines : {declarations_orphelines}")
    
    if declarations_orphelines > 0:
        print("\n❌ ATTENTION : Il reste des déclarations non liées !")
        orphelines = Declaration.objects.filter(tournoi__isnull=True)[:5]
        print("\nExemples :")
        for decl in orphelines:
            print(f"   - ID {decl.id}: {decl.club} | {decl.date_tournoi}")
        return False
    else:
        print("\n✅ Toutes les déclarations sont correctement liées !")
        return True

def afficher_stats_finales():
    """Affiche les statistiques finales"""
    print("\n" + "="*60)
    print("📈 STATISTIQUES FINALES")
    print("="*60)
    
    nb_tournois = Tournoi.objects.count()
    nb_declarations = Declaration.objects.count()
    
    print(f"\n🏆 Tournois créés           : {nb_tournois}")
    print(f"📋 Déclarations migrées     : {nb_declarations}")
    
    if nb_tournois > 0:
        from django.db.models import Count, Sum
        
        # Stats par tournoi
        tournois_stats = Tournoi.objects.annotate(
            nb_clubs=Count('declarations'),
            nb_equipes=Sum('declarations__nombre_equipes')
        ).order_by('-date')[:5]
        
        print("\n🔝 Top 5 derniers tournois :")
        print("-" * 60)
        for t in tournois_stats:
            print(f"   {t.date.strftime('%d/%m/%Y')} | "
                  f"{t.get_categorie_age_display()} {t.get_sexe_display()} | "
                  f"{t.nb_clubs} clubs, {t.nb_equipes or 0} équipes")

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("🚀 MIGRATION DECLARATIONS → TOURNOIS")
    print("="*60)
    
    try:
        # Étape 1 : Analyser
        groupes = analyser_declarations()
        if groupes is None:
            return
        
        # Confirmation
        print("\n" + "="*60)
        reponse = input("\n▶️  Voulez-vous continuer la migration ? (oui/non) : ").lower()
        if reponse not in ['oui', 'o', 'yes', 'y']:
            print("\n⏸️  Migration annulée par l'utilisateur.")
            return
        
        # Étape 2 : Créer les tournois (dans une transaction)
        with transaction.atomic():
            tournois_map = creer_tournois(groupes)
            
            # Étape 3 : Lier les déclarations
            nb_liees, nb_erreurs = lier_declarations_aux_tournois(groupes, tournois_map)
        
        # Étape 4 : Vérifier
        coherence_ok = verifier_coherence()
        
        # Étape 5 : Stats finales
        afficher_stats_finales()
        
        # Résumé
        print("\n" + "="*60)
        if coherence_ok and nb_erreurs == 0:
            print("✅ MIGRATION RÉUSSIE !")
        else:
            print("⚠️  MIGRATION TERMINÉE AVEC AVERTISSEMENTS")
        print("="*60)
        
        print("\n📝 Prochaines étapes :")
        print("   1. Vérifier dans l'admin Django : /admin/saisie_equipes/tournoi/")
        print("   2. Adapter les vues pour utiliser Tournoi")
        print("   3. (Optionnel) Supprimer le champ date_tournoi de Declaration")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
