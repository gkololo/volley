from django.shortcuts import render, redirect
from django.utils import timezone
from collections import defaultdict
from .forms import DeclarationForm
from .models import Declaration

def declaration_view(request):
    if request.method == "POST":
        form = DeclarationForm(request.POST)
        if form.is_valid():
            declaration = form.save()
            request.session["confirmation_data"] = {
                "declarant": declaration.declarant,
                "club": str(declaration.club),
                "nombre_equipes": declaration.nombre_equipes,
                "categorie_age": declaration.get_categorie_age_display(),
            }
            return redirect("confirmation")
    else:
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
        '-date_tournoi',
        'categorie_age',
        'sexe',
        'zone',
        'club__nom'
    )

    # Même logique que consultation_view
    tournois_passes = []
    groupes_par_date = defaultdict(list)

    for declaration in declarations_passees:
        groupes_par_date[declaration.date_tournoi].append(declaration)

    for date_tournoi, declarations_liste in groupes_par_date.items():
        categories = defaultdict(list)

        for decl in declarations_liste:
            cle_categorie = f"{decl.categorie_age}_{decl.sexe}_{decl.zone}"
            categories[cle_categorie].append(decl)

        tableau_synthese = []
        categories_detaillees = []
        total_general = 0

        for cle_categorie in sorted(categories.keys()):
            declarations_cat = categories[cle_categorie]
            premiere_decl = declarations_cat[0]

            total_equipes_cat = sum(d.nombre_equipes for d in declarations_cat)
            nb_clubs = len(declarations_cat)
            total_general += total_equipes_cat

            tableau_synthese.append({
                'categorie': premiere_decl.get_categorie_age_display(),
                'sexe': premiere_decl.get_sexe_display(),
                'zone': premiere_decl.get_zone_display() if premiere_decl.zone else "Toutes zones",
                'nb_clubs': nb_clubs,
                'total_equipes': total_equipes_cat,
                'cle': cle_categorie
            })

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

    tournois_passes.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'saisie_equipes/consultation_passee.html', {
        'tournois': tournois_passes,
        'type': 'passés',
    })