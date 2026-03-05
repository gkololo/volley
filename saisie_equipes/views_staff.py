"""
═══════════════════════════════════════════════════
🏢 VUES STAFF - INTERFACE D'ADMINISTRATION
═══════════════════════════════════════════════════

Toutes les vues pour l'interface staff (séparée de l'admin Django)
Accessible uniquement aux utilisateurs avec is_staff=True

VERSION 4 : Ajout consultation déclarations (Étape 4)
"""

import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .decorators import staff_or_superuser_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from .models import Candidature, Tournoi, Declaration, StatutCandidature
from .forms import TournoiForm


# ═══════════════════════════════════════════════════
# 🏠 DASHBOARD
# ═══════════════════════════════════════════════════

@staff_or_superuser_required
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
        statut=StatutCandidature.EN_ATTENTE
    ).select_related('tournoi', 'club')

    nb_candidatures_en_attente = candidatures_en_attente.count()

    nb_candidatures_validees = Candidature.objects.filter(
        statut=StatutCandidature.VALIDEE
    ).count()

    nb_candidatures_refusees = Candidature.objects.filter(
        statut=StatutCandidature.REFUSEE
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
    ).select_related('club_organisateur').annotate(
        nb_declarations_calculees=Count('declarations', distinct=True),
        nb_equipes_calculees=Sum('declarations__nombre_equipes'),
        nb_candidatures_calculees=Count('candidatures', distinct=True),
    ).order_by('date')[:5]

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


# ═══════════════════════════════════════════════════
# 🗓️ GESTION DES TOURNOIS
# ═══════════════════════════════════════════════════

@staff_or_superuser_required
def tournois_liste_view(request):
    """
    📋 Liste de tous les tournois avec filtres

    Filtres disponibles :
    - Période (tous, à venir, passés)
    - Statut (tous, planifié, confirmé, annulé, terminé)
    - Recherche par texte
    """
    today = timezone.now().date()

    # Récupérer tous les tournois
    tournois = Tournoi.objects.select_related('club_organisateur').order_by('-date')

    # ═══════════════════════════════════════════════════
    # FILTRES
    # ═══════════════════════════════════════════════════

    # Filtre période
    periode = request.GET.get('periode', 'tous')
    if periode == 'a_venir':
        tournois = tournois.filter(date__gte=today)
    elif periode == 'passes':
        tournois = tournois.filter(date__lt=today)

    # Filtre statut
    statut = request.GET.get('statut', 'tous')
    if statut != 'tous':
        tournois = tournois.filter(statut=statut)

    # Filtre recherche
    recherche = request.GET.get('q', '')
    if recherche:
        tournois = tournois.filter(
            Q(categorie_age__icontains=recherche) |
            Q(club_organisateur__nom__icontains=recherche) |
            Q(lieu__icontains=recherche)
        )

    # ═══════════════════════════════════════════════════
    # ENRICHISSEMENT DES DONNÉES
    # ═══════════════════════════════════════════════════

    tournois = tournois.annotate(
        nb_declarations_calculees=Count('declarations', distinct=True),
        nb_equipes_calculees=Sum('declarations__nombre_equipes'),
        nb_candidatures_calculees=Count('candidatures', distinct=True),
        nb_candidatures_en_attente=Count(
            'candidatures',
            filter=Q(candidatures__statut='EN_ATTENTE'),
            distinct=True
        ),
    )

    # ═══════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════

    nb_total = tournois.count()
    nb_a_venir = Tournoi.objects.filter(date__gte=today).count()
    nb_passes = Tournoi.objects.filter(date__lt=today).count()

    context = {
        'tournois': tournois,
        'periode': periode,
        'statut': statut,
        'recherche': recherche,
        'nb_total': nb_total,
        'nb_a_venir': nb_a_venir,
        'nb_passes': nb_passes,
    }

    return render(request, 'staff/tournoi_liste.html', context)


@staff_or_superuser_required
def tournoi_create_view(request):
    """
    ➕ Créer un nouveau tournoi
    """
    if request.method == 'POST':
        form = TournoiForm(request.POST)

        if form.is_valid():
            tournoi = form.save(commit=False)
            tournoi.created_by = request.user
            tournoi.save()

            messages.success(
                request,
                f"✅ Tournoi créé avec succès : {tournoi}"
            )

            return redirect('staff:tournois_liste')
    else:
        # Valeurs par défaut
        initial = {
            'statut': 'PLANIFIE',
            'est_publie': True,
        }
        form = TournoiForm(initial=initial)

    context = {
        'form': form,
        'action': 'Créer',
        'titre': 'Créer un nouveau tournoi',
    }

    return render(request, 'staff/tournoi_form.html', context)


@staff_or_superuser_required
def tournoi_edit_view(request, tournoi_id):
    """
    ✏️ Modifier un tournoi existant
    """
    tournoi = get_object_or_404(Tournoi, pk=tournoi_id)

    if request.method == 'POST':
        # Vérifier si c'est une suppression
        if 'delete' in request.POST:
            # Vérifier s'il y a des déclarations
            nb_declarations = tournoi.get_nb_declarations()

            if nb_declarations > 0:
                messages.error(
                    request,
                    f"❌ Impossible de supprimer ce tournoi : {nb_declarations} déclaration(s) associée(s). "
                    f"Changez plutôt le statut en 'Annulé'."
                )
            else:
                tournoi_str = str(tournoi)
                tournoi.delete()
                messages.success(
                    request,
                    f"🗑️ Tournoi supprimé : {tournoi_str}"
                )
                return redirect('staff:tournois_liste')
        else:
            # Modification normale
            form = TournoiForm(request.POST, instance=tournoi)

            if form.is_valid():
                tournoi = form.save()

                messages.success(
                    request,
                    f"💾 Tournoi modifié avec succès : {tournoi}"
                )

                return redirect('staff:tournois_liste')
    else:
        form = TournoiForm(instance=tournoi)

    # Statistiques du tournoi
    nb_declarations = tournoi.get_nb_declarations()
    nb_equipes = tournoi.get_nb_equipes_total()
    nb_candidatures = tournoi.get_nb_candidatures()
    nb_candidatures_en_attente = tournoi.get_candidatures_en_attente().count()

    context = {
        'form': form,
        'tournoi': tournoi,
        'action': 'Modifier',
        'titre': f'Modifier le tournoi : {tournoi}',
        'nb_declarations': nb_declarations,
        'nb_equipes': nb_equipes,
        'nb_candidatures': nb_candidatures,
        'nb_candidatures_en_attente': nb_candidatures_en_attente,
    }

    return render(request, 'staff/tournoi_form.html', context)


# ═══════════════════════════════════════════════════
# 📋 GESTION DES CANDIDATURES (ÉTAPE 3)
# ═══════════════════════════════════════════════════

@staff_or_superuser_required
def candidatures_liste_view(request):
    """
    📋 Liste de toutes les candidatures avec filtres

    Filtres disponibles :
    - Statut (tous, en attente, validées, refusées)
    - Tournoi (filtre par tournoi spécifique)
    - Recherche par club
    """
    # Récupérer toutes les candidatures
    candidatures = Candidature.objects.select_related(
        'tournoi', 'club', 'traite_par'
    ).order_by('-created_at')

    # ═══════════════════════════════════════════════════
    # FILTRES
    # ═══════════════════════════════════════════════════

    # Filtre statut
    statut = request.GET.get('statut', 'tous')
    if statut != 'tous':
        candidatures = candidatures.filter(statut=statut)

    # Filtre tournoi
    tournoi_id = request.GET.get('tournoi', '')
    if tournoi_id:
        candidatures = candidatures.filter(tournoi_id=tournoi_id)

    # Filtre recherche (club)
    recherche = request.GET.get('q', '')
    if recherche:
        candidatures = candidatures.filter(
            Q(club__nom__icontains=recherche) |
            Q(declarant__icontains=recherche) |
            Q(lieu__icontains=recherche)
        )

    # ═══════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════

    nb_total = candidatures.count()
    nb_en_attente = Candidature.objects.filter(statut=StatutCandidature.EN_ATTENTE).count()
    nb_validees = Candidature.objects.filter(statut=StatutCandidature.VALIDEE).count()
    nb_refusees = Candidature.objects.filter(statut=StatutCandidature.REFUSEE).count()

    # ═══════════════════════════════════════════════════
    # LISTE TOURNOIS POUR FILTRE
    # ═══════════════════════════════════════════════════

    tournois_avec_candidatures = Tournoi.objects.filter(
        candidatures__isnull=False
    ).distinct().order_by('-date')

    context = {
        'candidatures': candidatures,
        'statut': statut,
        'tournoi_id': tournoi_id,
        'recherche': recherche,
        'nb_total': nb_total,
        'nb_en_attente': nb_en_attente,
        'nb_validees': nb_validees,
        'nb_refusees': nb_refusees,
        'tournois_liste': tournois_avec_candidatures,
    }

    return render(request, 'staff/candidature_liste_staff.html', context)


@staff_or_superuser_required
def candidature_valider_view(request, candidature_id):
    """
    ✅ Valider une candidature et définir l'organisateur du tournoi

    Actions :
    - candidature.statut → VALIDEE
    - tournoi.club_organisateur → candidature.club
    - tournoi.lieu → candidature.lieu
    - tournoi.statut → CONFIRME
    """
    candidature = get_object_or_404(Candidature, pk=candidature_id)

    # Vérifier que la candidature est bien en attente
    if candidature.statut != StatutCandidature.EN_ATTENTE:
        messages.warning(
            request,
            f"⚠️ Cette candidature a déjà été traitée : {candidature.get_statut_display()}"
        )
        return redirect('staff:candidatures_liste')

    if request.method == 'POST':
        # Confirmer la validation
        if 'confirmer' in request.POST:
            try:
                # Utiliser la méthode du modèle
                candidature.valider(request.user)

                messages.success(
                    request,
                    f"✅ Candidature validée avec succès ! "
                    f"{candidature.club.nom} organisera le tournoi {candidature.tournoi} "
                    f"au {candidature.lieu}."
                )

                return redirect('staff:candidatures_liste')

            except Exception as e:
                messages.error(
                    request,
                    f"❌ Erreur lors de la validation : {str(e)}"
                )

    # Vérifier s'il y a d'autres candidatures pour ce tournoi
    autres_candidatures = Candidature.objects.filter(
        tournoi=candidature.tournoi,
        statut=StatutCandidature.EN_ATTENTE
    ).exclude(pk=candidature.pk).count()

    context = {
        'candidature': candidature,
        'tournoi': candidature.tournoi,
        'autres_candidatures': autres_candidatures,
    }

    return render(request, 'staff/candidature_valider_confirm.html', context)


@staff_or_superuser_required
def candidature_refuser_view(request, candidature_id):
    """
    ❌ Refuser une candidature avec raison
    """
    candidature = get_object_or_404(Candidature, pk=candidature_id)

    # Vérifier que la candidature est bien en attente
    if candidature.statut != StatutCandidature.EN_ATTENTE:
        messages.warning(
            request,
            f"⚠️ Cette candidature a déjà été traitée : {candidature.get_statut_display()}"
        )
        return redirect('staff:candidatures_liste')

    if request.method == 'POST':
        raison = request.POST.get('raison_refus', '').strip()

        if not raison:
            messages.error(
                request,
                "❌ Veuillez indiquer une raison pour le refus."
            )
        else:
            try:
                # Utiliser la méthode du modèle
                candidature.refuser(request.user, raison)

                messages.success(
                    request,
                    f"✅ Candidature de {candidature.club.nom} refusée. "
                    f"Le club sera informé de la décision."
                )

                return redirect('staff:candidatures_liste')

            except Exception as e:
                messages.error(
                    request,
                    f"❌ Erreur lors du refus : {str(e)}"
                )

    context = {
        'candidature': candidature,
        'tournoi': candidature.tournoi,
    }

    return render(request, 'staff/candidature_refuser_form.html', context)


# ═══════════════════════════════════════════════════
# 📊 CONSULTATION DÉCLARATIONS (ÉTAPE 4)
# ═══════════════════════════════════════════════════

@staff_or_superuser_required
def declarations_liste_view(request):
    """
    📊 Liste de toutes les déclarations avec filtres

    Filtres disponibles :
    - Tournoi (filtre par tournoi spécifique)
    - Club (filtre par club)
    - Catégorie (M11, M13, M15, M18)
    - Zone (Nord, Sud, Aucune)
    - Recherche par texte

    Fonctionnalités :
    - Statistiques (total déclarations, équipes, clubs)
    - Tri par date déclaration (desc)
    - Export CSV optionnel
    """
    # Récupérer toutes les déclarations
    declarations = Declaration.objects.select_related(
        'club', 'tournoi'
    ).order_by('-date_declaration')

    # ═══════════════════════════════════════════════════
    # FILTRES
    # ═══════════════════════════════════════════════════

    # Filtre tournoi
    tournoi_id = request.GET.get('tournoi', '')
    if tournoi_id:
        declarations = declarations.filter(tournoi_id=tournoi_id)

    # Filtre club
    club_id = request.GET.get('club', '')
    if club_id:
        declarations = declarations.filter(club_id=club_id)

    # Filtre catégorie
    categorie = request.GET.get('categorie', '')
    if categorie:
        declarations = declarations.filter(tournoi__categorie_age=categorie)

    # Filtre sexe
    sexe = request.GET.get('sexe', '')
    if sexe:
        declarations = declarations.filter(tournoi__sexe=sexe)

    # Filtre zone
    zone = request.GET.get('zone', '')
    if zone:
        declarations = declarations.filter(tournoi__zone=zone)

    # Filtre recherche
    recherche = request.GET.get('q', '')
    if recherche:
        declarations = declarations.filter(
            Q(club__nom__icontains=recherche) |
            Q(declarant__icontains=recherche) |
            Q(remarques__icontains=recherche)
        )

    # ═══════════════════════════════════════════════════
    # EXPORT CSV (si demandé)
    # ═══════════════════════════════════════════════════

    if request.GET.get('export') == 'csv':
        # Créer la réponse CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="declarations_volleychamp.csv"'

        # BOM UTF-8 pour Excel
        response.write('\ufeff')

        writer = csv.writer(response, delimiter=';')

        # En-têtes
        writer.writerow([
            'Date déclaration',
            'Club',
            'Déclarant',
            'Email',
            'Tournoi',
            'Date tournoi',
            'Catégorie',
            'Sexe',
            'Zone',
            'Nombre équipes',
            'Remarques'
        ])

        # Données
        for d in declarations:
            writer.writerow([
                d.date_declaration.strftime('%d/%m/%Y %H:%M'),
                d.club.nom,
                d.declarant,
                d.email_club,
                str(d.tournoi),
                d.tournoi.date.strftime('%d/%m/%Y'),
                d.tournoi.get_categorie_age_display(),
                d.tournoi.get_sexe_display(),
                d.tournoi.get_zone_display() if d.tournoi.zone else 'Toutes zones',
                d.nombre_equipes,
                d.remarques if d.remarques else ''
            ])

        return response

    # ═══════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════

    nb_total = declarations.count()

    # Nombre total d'équipes
    nb_equipes_total = declarations.aggregate(
        total=Sum('nombre_equipes')
    )['total'] or 0

    # Nombre de clubs distincts
    nb_clubs = declarations.values('club').distinct().count()

    # Nombre de tournois distincts
    nb_tournois = declarations.values('tournoi').distinct().count()

    # Répartition par catégorie
    repartition_categories = declarations.values('tournoi__categorie_age').annotate(
        count=Count('id'),
        equipes=Sum('nombre_equipes')
    ).order_by('tournoi__categorie_age')

    # ═══════════════════════════════════════════════════
    # LISTES POUR FILTRES
    # ═══════════════════════════════════════════════════

    # Tournois ayant des déclarations
    tournois_liste = Tournoi.objects.filter(
        declarations__isnull=False
    ).distinct().order_by('-date')

    # Clubs ayant déclaré
    clubs_liste = Declaration.objects.values_list(
        'club__id', 'club__nom'
    ).distinct().order_by('club__nom')

    context = {
        'declarations': declarations,
        'tournoi_id': tournoi_id,
        'club_id': club_id,
        'categorie': categorie,
        'sexe': sexe,
        'zone': zone,
        'recherche': recherche,
        'nb_total': nb_total,
        'nb_equipes_total': nb_equipes_total,
        'nb_clubs': nb_clubs,
        'nb_tournois': nb_tournois,
        'repartition_categories': repartition_categories,
        'tournois_liste': tournois_liste,
        'clubs_liste': clubs_liste,
    }

    return render(request, 'staff/declaration_liste_staff.html', context)
