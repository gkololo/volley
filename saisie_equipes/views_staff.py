"""
═══════════════════════════════════════════════════
🏢 VUES STAFF - INTERFACE D'ADMINISTRATION
═══════════════════════════════════════════════════

Toutes les vues pour l'interface staff (séparée de l'admin Django)
Accessible uniquement aux utilisateurs avec is_staff=True
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Sum

from .models import Candidature, Tournoi, Declaration


@staff_member_required
def dashboard_view(request):
    """
    📊 Dashboard principal du staff
    
    Affiche :
    - Statistiques sur les candidatures (en attente, validées, refusées)
    - Statistiques sur les tournois (à venir, total)
    - Statistiques sur les déclarations (total équipes, clubs)
    - Liste des prochains tournois
    - Actions rapides
    """
    today = timezone.now().date()
    
    # ═══════════════════════════════════════════════════
    # 📋 STATISTIQUES CANDIDATURES
    # ═══════════════════════════════════════════════════
    
    candidatures_en_attente = Candidature.objects.filter(
        statut='EN_ATTENTE'
    ).select_related('tournoi', 'club')
    
    nb_candidatures_en_attente = candidatures_en_attente.count()
    
    nb_candidatures_validees = Candidature.objects.filter(
        statut='VALIDEE'
    ).count()
    
    nb_candidatures_refusees = Candidature.objects.filter(
        statut='REFUSEE'
    ).count()
    
    nb_candidatures_total = Candidature.objects.count()
    
    # ═══════════════════════════════════════════════════
    # 🗓️ STATISTIQUES TOURNOIS
    # ═══════════════════════════════════════════════════
    
    nb_tournois_a_venir = Tournoi.objects.filter(
        date__gte=today,
        est_publie=True
    ).count()
    
    nb_tournois_planifies = Tournoi.objects.filter(
        statut='PLANIFIE',
        est_publie=True
    ).count()
    
    nb_tournois_confirmes = Tournoi.objects.filter(
        statut='CONFIRME',
        est_publie=True
    ).count()
    
    nb_tournois_total = Tournoi.objects.filter(
        est_publie=True
    ).count()
    
    # ═══════════════════════════════════════════════════
    # 📊 STATISTIQUES DÉCLARATIONS
    # ═══════════════════════════════════════════════════
    
    nb_declarations_total = Declaration.objects.count()
    
    # Nombre total d'équipes déclarées
    nb_equipes_total = Declaration.objects.aggregate(
        total=Sum('nombre_equipes')
    )['total'] or 0
    
    # Nombre de clubs ayant déclaré
    nb_clubs_declarants = Declaration.objects.values('club').distinct().count()
    
    # ═══════════════════════════════════════════════════
    # 📅 PROCHAINS TOURNOIS
    # ═══════════════════════════════════════════════════
    
    prochains_tournois = Tournoi.objects.filter(
        date__gte=today,
        est_publie=True
    ).select_related('club_organisateur').order_by('date')[:5]
    
    # Enrichir avec le nombre de déclarations
    for tournoi in prochains_tournois:
        tournoi.nb_declarations_calculees = tournoi.get_nb_declarations()
        tournoi.nb_equipes_calculees = tournoi.get_nb_equipes_total()
        tournoi.nb_candidatures_calculees = tournoi.get_nb_candidatures()
    
    # ═══════════════════════════════════════════════════
    # 🚨 CANDIDATURES EN ATTENTE (TOP 5)
    # ═══════════════════════════════════════════════════
    
    candidatures_recentes = candidatures_en_attente.order_by('-created_at')[:5]
    
    # ═══════════════════════════════════════════════════
    # 📦 CONTEXTE
    # ═══════════════════════════════════════════════════
    
    context = {
        # Candidatures
        'nb_candidatures_en_attente': nb_candidatures_en_attente,
        'nb_candidatures_validees': nb_candidatures_validees,
        'nb_candidatures_refusees': nb_candidatures_refusees,
        'nb_candidatures_total': nb_candidatures_total,
        'candidatures_recentes': candidatures_recentes,
        
        # Tournois
        'nb_tournois_a_venir': nb_tournois_a_venir,
        'nb_tournois_planifies': nb_tournois_planifies,
        'nb_tournois_confirmes': nb_tournois_confirmes,
        'nb_tournois_total': nb_tournois_total,
        'prochains_tournois': prochains_tournois,
        
        # Déclarations
        'nb_declarations_total': nb_declarations_total,
        'nb_equipes_total': nb_equipes_total,
        'nb_clubs_declarants': nb_clubs_declarants,
        
        # User info
        'user': request.user,
    }
    
    return render(request, 'staff/dashboard.html', context)
