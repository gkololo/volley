from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import logout
from datetime import datetime, timedelta
from django.http import Http404
import json  # 🆕 Pour sérialiser les poules en JSON

from .forms import DeclarationForm, CandidatureForm
from .models import Declaration, Tournoi, Candidature


def test_404(request):
    raise Http404("Page de test pour 404")


def accueil_view(request):
    """Page d'accueil avec navigation principale"""
    today = timezone.now().date()

    # ✨ NOUVEAU : Utiliser les objets Tournoi directement
    tournois_a_venir = Tournoi.objects.filter(
        date__gte=today,
        est_publie=True
    ).count()

    tournois_passes = Tournoi.objects.filter(
        date__lt=today,
        est_publie=True
    ).count()

    total_declarations = Declaration.objects.count()

    context = {
        'tournois_a_venir': tournois_a_venir,
        'tournois_passes': tournois_passes,
        'total_declarations': total_declarations,
    }

    return render(request, 'saisie_equipes/accueil.html', context)


def declaration_view(request):
    """Formulaire de déclaration d'équipe"""

    # 🆕 Préparer les données des poules par tournoi (nécessaire pour GET et POST)
    tournois_poules = {}
    for tournoi in Tournoi.objects.filter(est_publie=True):
        tournois_poules[tournoi.id] = tournoi.poules_disponibles or []

    if request.method == "POST":
        # 🕐 VÉRIFICATION TEMPORELLE - Anti-robot
        form_start_time = request.session.get('form_start_time')
        if form_start_time:
            try:
                start_time = datetime.fromisoformat(form_start_time)
                elapsed = timezone.now().replace(tzinfo=None) - start_time

                # Trop rapide = robot probable
                if elapsed < timedelta(seconds=3):
                    messages.error(request, "⚠️ Veuillez prendre le temps de remplir le formulaire correctement.")
                    return redirect("declaration")

                # Trop lent = session expirée
                if elapsed > timedelta(minutes=30):
                    messages.warning(request, "⏰ Session expirée pour des raisons de sécurité. Veuillez recommencer.")
                    return redirect("declaration")

            except (ValueError, TypeError):
                messages.warning(request, "Session invalide détectée. Formulaire réinitialisé.")
                return redirect("declaration")

        # 📊 LIMITATION PAR IP - Anti-spam
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        session_key = f'submissions_{ip_address.replace(".", "_")}'
        submissions_today = request.session.get(session_key, 0)

        if submissions_today >= 5:
            messages.error(request, "🚫 Vous avez atteint la limite de déclarations pour cette session. Réessayez plus tard.")
            return redirect("declaration")

        # 🔍 TRAITEMENT DU FORMULAIRE
        form = DeclarationForm(request.POST)
        if form.is_valid():
            try:
                declaration = form.save()

                # 📈 COMPTEUR DE SOUMISSIONS
                request.session[session_key] = submissions_today + 1
                request.session.set_expiry(3600)

                # 🧹 NETTOYER LA SESSION
                if 'form_start_time' in request.session:
                    del request.session['form_start_time']

                # ✅ DONNÉES DE CONFIRMATION
                request.session["confirmation_data"] = {
                    "declarant": declaration.declarant,
                    "club": str(declaration.club),
                    "nombre_equipes": declaration.nombre_equipes,
                    "categorie_age": declaration.get_categorie_age_display(),
                }

                messages.success(request, f"✅ Déclaration enregistrée avec succès pour {declaration.club}!")
                return redirect("confirmation")

            except Exception as e:
                messages.error(request, "❌ Erreur lors de l'enregistrement. Veuillez réessayer.")
                print(f"Erreur sauvegarde déclaration: {e}")
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs signalées ci-dessous.")
    else:
        # 🆕 NOUVEAU FORMULAIRE
        request.session['form_start_time'] = timezone.now().replace(tzinfo=None).isoformat()
        form = DeclarationForm()

    # 🆕 Contexte enrichi avec les poules par tournoi
    context = {
        "form": form,
        "tournois_poules_json": json.dumps(tournois_poules),  # 🆕 Pour window.TOURNOIS_POULES
    }

    return render(request, "saisie_equipes/declaration_form.html", context)


def confirmation_view(request):
    """Page de confirmation après déclaration"""
    confirmation_data = request.session.pop("confirmation_data", {})
    return render(request, "saisie_equipes/confirmation.html", {"data": confirmation_data})


def consultation_view(request):
    """
    ✨ NOUVEAU : Version simplifiée utilisant les objets Tournoi

    Au lieu de regrouper manuellement les déclarations,
    on charge directement les tournois avec leurs déclarations.
    """
    today = timezone.now().date()

    # 🎯 Charger les tournois à venir avec leurs déclarations
    tournois = Tournoi.objects.filter(
        date__gte=today,
        est_publie=True
    ).prefetch_related(
        'declarations__club'  # Optimisation : charge les clubs en une seule requête
    ).order_by('date', 'categorie_age', 'sexe')

    return render(request, "saisie_equipes/consultation.html", {
        "tournois": tournois,
        "type": "à venir",
    })


def consultation_passee_view(request):
    """
    ✨ NOUVEAU : Version simplifiée pour les tournois passés
    """
    today = timezone.now().date()

    # 🎯 Charger les tournois passés avec leurs déclarations
    tournois = Tournoi.objects.filter(
        date__lt=today,
        est_publie=True
    ).prefetch_related(
        'declarations__club'
    ).order_by('-date', 'categorie_age', 'sexe')

    return render(request, 'saisie_equipes/consultation_passee.html', {
        'tournois': tournois,
        'type': 'passés',
    })

def candidature_liste_view(request):
    """
    Liste des tournois disponibles pour candidater

    Affiche les tournois à venir publiés avec leur statut :
    - Nombre de candidatures en attente
    - Si organisateur déjà assigné
    - Possibilité de candidater
    """
    today = timezone.now().date()

    # Charger les tournois à venir publiés
    tournois = Tournoi.objects.filter(
        date__gte=today,
        est_publie=True
    ).prefetch_related('candidatures').order_by('date', 'categorie_age', 'sexe')

    # Enrichir chaque tournoi avec des infos supplémentaires
    tournois_enrichis = []
    for tournoi in tournois:
        # Compter les candidatures
        nb_candidatures = tournoi.candidatures.exclude(statut='RETIREE').count()
        nb_en_attente = tournoi.candidatures.filter(statut='EN_ATTENTE').count()

        # Vérifier si ouvert aux candidatures
        peut_candidater = tournoi.peut_recevoir_candidatures() and not tournoi.a_organisateur()

        tournois_enrichis.append({
            'tournoi': tournoi,
            'nb_candidatures': nb_candidatures,
            'nb_en_attente': nb_en_attente,
            'peut_candidater': peut_candidater,
            'a_organisateur': tournoi.a_organisateur()
        })

    return render(request, 'saisie_equipes/candidature_liste.html', {
        'tournois_enrichis': tournois_enrichis,
    })


def candidature_form_view(request, tournoi_id):
    """
    Formulaire de candidature pour un tournoi spécifique

    Args:
        tournoi_id: ID du tournoi pour lequel candidater
    """
    tournoi = get_object_or_404(Tournoi, pk=tournoi_id)

    # Vérifier que le tournoi accepte encore les candidatures
    if not tournoi.peut_recevoir_candidatures():
        messages.error(request, "❌ Ce tournoi n'accepte plus de candidatures.")
        return redirect('candidature_liste')

    # Vérifier qu'il n'y a pas déjà un organisateur
    if tournoi.a_organisateur():
        messages.warning(request, f"⚠️ Ce tournoi a déjà un organisateur : {tournoi.club_organisateur}")
        return redirect('candidature_liste')

    if request.method == 'POST':
        form = CandidatureForm(request.POST)

        if form.is_valid():
            try:
                candidature = form.save()

                messages.success(
                    request,
                    f"✅ Candidature enregistrée avec succès pour le tournoi du "
                    f"{tournoi.date.strftime('%d/%m/%Y')} ! "
                    f"Vous serez contacté une fois votre candidature traitée."
                )

                return redirect('candidature_liste')

            except Exception as e:
                messages.error(request, "❌ Erreur lors de l'enregistrement. Veuillez réessayer.")
                print(f"Erreur sauvegarde candidature: {e}")
        else:
            messages.error(request, "❌ Veuillez corriger les erreurs signalées ci-dessous.")
    else:
        # Pré-remplir le formulaire avec le tournoi
        form = CandidatureForm(initial={'tournoi': tournoi})

    return render(request, 'saisie_equipes/candidature_form.html', {
        'form': form,
        'tournoi': tournoi,
    })


def mes_candidatures_view(request):
    """
    Liste des candidatures (filtrable par club si souhaité)

    Pour l'instant, affiche toutes les candidatures.
    Plus tard, on pourra filtrer par club si authentification.
    """
    # Charger toutes les candidatures récentes
    candidatures = Candidature.objects.select_related(
        'tournoi',
        'club',
        'traite_par'
    ).order_by('-created_at')

    # Grouper par statut
    en_attente = candidatures.filter(statut='EN_ATTENTE')
    validees = candidatures.filter(statut='VALIDEE')
    refusees = candidatures.filter(statut='REFUSEE')
    retirees = candidatures.filter(statut='RETIREE')

    return render(request, 'saisie_equipes/mes_candidatures.html', {
        'candidatures_en_attente': en_attente,
        'candidatures_validees': validees,
        'candidatures_refusees': refusees,
        'candidatures_retirees': retirees,
        'total': candidatures.count(),
    })

def logout_view(request):
    """Déconnexion utilisateur"""
    username = request.user.get_full_name() or request.user.username if request.user.is_authenticated else None
    logout(request)
    if username:
        messages.success(request, f"👋 Au revoir {username} ! Vous êtes maintenant déconnecté.")
    else:
        messages.success(request, "👋 Vous êtes maintenant déconnecté.")
    return redirect('accueil')
