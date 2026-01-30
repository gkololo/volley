"""
═══════════════════════════════════════════════════
🔗 URLS STAFF - ROUTAGE INTERFACE STAFF
═══════════════════════════════════════════════════

Toutes les URLs commençant par /staff/

VERSION 3 : Ajout routes candidatures (Étape 3)
"""

from django.urls import path
from .views_staff import (
    # Dashboard
    dashboard_view,
    
    # Gestion Tournois (Étape 2)
    tournois_liste_view,
    tournoi_create_view,
    tournoi_edit_view,
    
    # Gestion Candidatures (Étape 3)
    candidatures_liste_view,
    candidature_valider_view,
    candidature_refuser_view,
)

# Namespace pour les URLs staff
app_name = 'staff'

urlpatterns = [
    # ═══════════════════════════════════════════════════
    # 🏠 DASHBOARD
    # ═══════════════════════════════════════════════════
    path('', dashboard_view, name='dashboard'),
    
    # ═══════════════════════════════════════════════════
    # 🗓️ GESTION TOURNOIS (Étape 2)
    # ═══════════════════════════════════════════════════
    path('tournois/', tournois_liste_view, name='tournois_liste'),
    path('tournois/nouveau/', tournoi_create_view, name='tournoi_create'),
    path('tournois/<int:tournoi_id>/edit/', tournoi_edit_view, name='tournoi_edit'),
    
    # ═══════════════════════════════════════════════════
    # 📋 GESTION CANDIDATURES (Étape 3)
    # ═══════════════════════════════════════════════════
    path('candidatures/', candidatures_liste_view, name='candidatures_liste'),
    path('candidatures/<int:candidature_id>/valider/', candidature_valider_view, name='candidature_valider'),
    path('candidatures/<int:candidature_id>/refuser/', candidature_refuser_view, name='candidature_refuser'),
    
    # ═══════════════════════════════════════════════════
    # 📊 CONSULTATION DÉCLARATIONS (Étape 4 - à venir)
    # ═══════════════════════════════════════════════════
    # path('declarations/', declarations_liste_view, name='declarations_liste'),
]
