from django.shortcuts import render, redirect
from django.utils import timezone
from collections import defaultdict
from .forms import DeclarationForm
from .models import Declaration
from django.contrib import messages
from datetime import datetime, timedelta  # ← AJOUT IMPORTANT
from django.http import Http404


def test_404(request):
    raise Http404("Page de test pour 404")



def accueil_view(request):
    """Page d'accueil avec navigation principale"""
    # Quelques statistiques pour rendre la page vivante
    today = timezone.now().date()

    # Compter les tournois à venir et passés
    tournois_a_venir = Declaration.objects.filter(date_tournoi__gte=today).values('date_tournoi').distinct().count()
    tournois_passes = Declaration.objects.filter(date_tournoi__lt=today).values('date_tournoi').distinct().count()
    total_declarations = Declaration.objects.count()

    context = {
        'tournois_a_venir': tournois_a_venir,
        'tournois_passes': tournois_passes,
        'total_declarations': total_declarations,
    }

    return render(request, 'saisie_equipes/accueil.html', context)

def declaration_view(request):
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
                # Session corrompue
                messages.warning(request, "Session invalide détectée. Formulaire réinitialisé.")
                return redirect("declaration")

        # 📊 LIMITATION PAR IP - Anti-spam
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        session_key = f'submissions_{ip_address.replace(".", "_")}'
        submissions_today = request.session.get(session_key, 0)

        if submissions_today >= 5:  # Maximum 5 soumissions par IP/session
            messages.error(request, "🚫 Vous avez atteint la limite de déclarations pour cette session. Réessayez plus tard.")
            return redirect("declaration")

        # 📝 TRAITEMENT DU FORMULAIRE
        form = DeclarationForm(request.POST)
        if form.is_valid():
            try:
                declaration = form.save()

                # 📈 COMPTEUR DE SOUMISSIONS (succès uniquement)
                request.session[session_key] = submissions_today + 1
                request.session.set_expiry(3600)  # Expire dans 1 heure

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
            # 🚨 ERREURS DE VALIDATION
            messages.error(request, "❌ Veuillez corriger les erreurs signalées ci-dessous.")
    else:
        # 🆕 NOUVEAU FORMULAIRE
        # Marquer le début du remplissage pour vérification temporelle
        request.session['form_start_time'] = timezone.now().replace(tzinfo=None).isoformat()
        form = DeclarationForm()

    return render(request, "saisie_equipes/declaration_form.html", {"form": form})

def confirmation_view(request):
    confirmation_data = request.session.pop("confirmation_data", {})
    return render(request, "saisie_equipes/confirmation.html", {"data": confirmation_data})

def consultation_view(request):
    today = timezone.now().date()

    declarations = Declaration.objects.filter(
        date_tournoi__gte=today
    ).order_by(
        "date_tournoi",
        "categorie_age",
        "sexe",
        "zone",
        "club__nom"
    )

    # 🎯 NOUVELLE LOGIQUE : Grouper par date, puis par catégorie
    tournois = []
    groupes_par_date = defaultdict(list)

    # Étape 1 : Grouper par date
    for d in declarations:
        groupes_par_date[d.date_tournoi].append(d)

    # Étape 2 : Pour chaque date, créer la structure complète
    for date_tournoi, declarations_liste in groupes_par_date.items():

        # Grouper par catégorie + sexe + zone
        categories = defaultdict(list)

        for decl in declarations_liste:
            # Créer une clé unique pour chaque catégorie/sexe/zone
            cle_categorie = f"{decl.categorie_age}_{decl.sexe}_{decl.zone}"
            categories[cle_categorie].append(decl)

        # Créer le tableau de synthèse pour cette date
        tableau_synthese = []
        categories_detaillees = []
        total_general = 0

        # Trier les catégories pour un affichage logique
        for cle_categorie in sorted(categories.keys()):
            declarations_cat = categories[cle_categorie]

            # Infos de la première déclaration pour les métadonnées
            premiere_decl = declarations_cat[0]

            # Calculer les totaux pour cette catégorie
            total_equipes_cat = sum(d.nombre_equipes for d in declarations_cat)
            nb_clubs = len(declarations_cat)

            total_general += total_equipes_cat

            # Ligne du tableau de synthèse
            tableau_synthese.append({
                'categorie': premiere_decl.get_categorie_age_display(),
                'sexe': premiere_decl.get_sexe_display(),
                'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
                'nb_clubs': nb_clubs,
                'total_equipes': total_equipes_cat,
                'cle': cle_categorie  # Pour les liens ancres
            })

            # Détails de la catégorie
            categories_detaillees.append({
                'categorie': premiere_decl.get_categorie_age_display(),
                'sexe': premiere_decl.get_sexe_display(),
                'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
                'declarations': sorted(declarations_cat, key=lambda x: x.club.nom),
                'total_equipes': total_equipes_cat,
                'nb_clubs': nb_clubs,
                'cle': cle_categorie
            })

        tournois.append({
            'date': date_tournoi,
            'tableau_synthese': tableau_synthese,
            'categories_detaillees': categories_detaillees,
            'total_general': total_general,
            'nb_categories': len(tableau_synthese),
            'nb_clubs_total': len(declarations_liste)
        })

    # Trier les tournois par date
    tournois.sort(key=lambda x: x['date'])

    return render(request, "saisie_equipes/consultation.html", {
        "tournois": tournois,
        "type": "à venir",
    })

def consultation_passee_view(request):
    today = timezone.now().date()

    declarations_passees = Declaration.objects.filter(
        date_tournoi__lt=today
    ).order_by(
        '-date_tournoi',          # Du plus récent au plus ancien
        'categorie_age',
        'sexe',
        'zone',
        'club__nom'
    )

    # 📊 MÊME LOGIQUE que consultation_view
    tournois_passes = []
    groupes_par_date = defaultdict(list)

    # Étape 1 : Grouper par date
    for declaration in declarations_passees:
        groupes_par_date[declaration.date_tournoi].append(declaration)

    # Étape 2 : Pour chaque date, créer la structure complète
    for date_tournoi, declarations_liste in groupes_par_date.items():

        # Grouper par catégorie + sexe + zone
        categories = defaultdict(list)

        for decl in declarations_liste:
            cle_categorie = f"{decl.categorie_age}_{decl.sexe}_{decl.zone}"
            categories[cle_categorie].append(decl)

        # Créer le tableau de synthèse pour cette date
        tableau_synthese = []
        categories_detaillees = []
        total_general = 0

        # Trier les catégories pour un affichage logique
        for cle_categorie in sorted(categories.keys()):
            declarations_cat = categories[cle_categorie]
            premiere_decl = declarations_cat[0]

            # Calculer les totaux pour cette catégorie
            total_equipes_cat = sum(d.nombre_equipes for d in declarations_cat)
            nb_clubs = len(declarations_cat)
            total_general += total_equipes_cat

            # Ligne du tableau de synthèse
            tableau_synthese.append({
                'categorie': premiere_decl.get_categorie_age_display(),
                'sexe': premiere_decl.get_sexe_display(),
                'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
                'nb_clubs': nb_clubs,
                'total_equipes': total_equipes_cat,
                'cle': cle_categorie
            })

            # Détails de la catégorie
            categories_detaillees.append({
                'categorie': premiere_decl.get_categorie_age_display(),
                'sexe': premiere_decl.get_sexe_display(),
                'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
                'declarations': sorted(declarations_cat, key=lambda x: x.club.nom),
                'total_equipes': total_equipes_cat,
                'nb_clubs': nb_clubs,
                'cle': cle_categorie
            })

        tournois_passes.append({
            'date': date_tournoi,
            'tableau_synthese': tableau_synthese,
            'categories_detaillees': categories_detaillees,
            'total_general': total_general,
            'nb_categories': len(tableau_synthese),
            'nb_clubs_total': len(declarations_liste)
        })

    # Trier par date décroissante (plus récent en premier)
    tournois_passes.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'saisie_equipes/consultation_passee.html', {
        'tournois': tournois_passes,
        'type': 'passés',
    })