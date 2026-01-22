"""
Custom template tags pour les statistiques de tournois
"""
from django import template
from collections import defaultdict

register = template.Library()


@register.filter
def get_tableau_synthese(tournoi):
    """
    Génère le tableau de synthèse pour un tournoi
    
    Returns:
        list: Liste de dictionnaires avec les stats par catégorie
    """
    declarations = tournoi.declarations.all()
    
    if not declarations:
        return []
    
    # Grouper par catégorie + sexe + zone
    categories = defaultdict(list)
    for decl in declarations:
        cle = f"{decl.categorie_age}_{decl.sexe}_{decl.zone or ''}"
        categories[cle].append(decl)
    
    # Créer le tableau de synthèse
    tableau = []
    for cle in sorted(categories.keys()):
        declarations_cat = categories[cle]
        premiere_decl = declarations_cat[0]
        
        total_equipes = sum(d.nombre_equipes for d in declarations_cat)
        nb_clubs = len(declarations_cat)
        
        tableau.append({
            'categorie': premiere_decl.get_categorie_age_display(),
            'sexe': premiere_decl.get_sexe_display(),
            'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
            'nb_clubs': nb_clubs,
            'total_equipes': total_equipes,
            'cle': cle
        })
    
    return tableau


@register.filter
def get_categories_detaillees(tournoi):
    """
    Génère les détails par catégorie pour un tournoi
    
    Returns:
        list: Liste de dictionnaires avec les déclarations groupées
    """
    declarations = tournoi.declarations.all()
    
    if not declarations:
        return []
    
    # Grouper par catégorie + sexe + zone
    categories = defaultdict(list)
    for decl in declarations:
        cle = f"{decl.categorie_age}_{decl.sexe}_{decl.zone or ''}"
        categories[cle].append(decl)
    
    # Créer les détails
    details = []
    for cle in sorted(categories.keys()):
        declarations_cat = categories[cle]
        premiere_decl = declarations_cat[0]
        
        total_equipes = sum(d.nombre_equipes for d in declarations_cat)
        nb_clubs = len(declarations_cat)
        
        details.append({
            'categorie': premiere_decl.get_categorie_age_display(),
            'sexe': premiere_decl.get_sexe_display(),
            'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
            'declarations': sorted(declarations_cat, key=lambda x: x.club.nom),
            'total_equipes': total_equipes,
            'nb_clubs': nb_clubs,
            'cle': cle
        })
    
    return details


@register.filter
def get_total_general(tournoi):
    """Calcule le nombre total d'équipes pour un tournoi"""
    from django.db.models import Sum
    total = tournoi.declarations.aggregate(total=Sum('nombre_equipes'))['total']
    return total or 0


@register.filter
def get_nb_clubs_total(tournoi):
    """Calcule le nombre de clubs ayant déclaré des équipes"""
    return tournoi.declarations.values('club').distinct().count()


@register.filter
def get_nb_categories(tournoi):
    """Calcule le nombre de catégories différentes"""
    declarations = tournoi.declarations.all()
    
    if not declarations:
        return 0
    
    # Compter les combinaisons uniques de catégorie + sexe + zone
    categories = set()
    for decl in declarations:
        cle = f"{decl.categorie_age}_{decl.sexe}_{decl.zone or ''}"
        categories.add(cle)
    
    return len(categories)
