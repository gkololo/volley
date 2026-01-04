import csv
import io
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from .models import Declaration, CategorieAge, Sexe, Zone, Club

# ═══════════════════════════════════════════════════
# 🎨 PERSONNALISATION DU TITRE DE L'ADMIN
# ═══════════════════════════════════════════════════

admin.site.site_header = "Administration VolleyChamp"  # ← Titre en haut
admin.site.site_title = "VolleyChamp Admin"           # ← Titre de l'onglet navigateur
admin.site.index_title = "Gestion du championnat"     # ← Titre page d'accueil

# Register your models here.
@admin.register(Declaration)
class DeclarationAdmin(admin.ModelAdmin):
    list_display = ("club", "declarant", "nombre_equipes", "categorie_age", "sexe", "zone", "date_tournoi")
    list_filter = ("categorie_age", "sexe", "zone", "date_tournoi")
    search_fields = ("club__nom", "declarant")
    date_hierarchy = "date_tournoi"

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['nom']
    search_fields = ['nom']
    ordering = ['nom']

    # Action pour télécharger le template CSV
    actions = ['export_template_csv']

    def export_template_csv(self, request, queryset):
        """Télécharge un template CSV pour l'import des clubs"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="template_clubs.csv"'

        writer = csv.writer(response)
        # En-tête
        writer.writerow(['nom_club'])
        # Exemples
        writer.writerow(['Racing Club de l\'Ouest'])
        writer.writerow(['Tampon Gecko Volley'])
        writer.writerow(['Club de Saint-Denis'])
        writer.writerow(['AS Saint-Pierre'])
        writer.writerow(['Volley Club du Port'])

        self.message_user(request, "📥 Template téléchargé. Utilisez 'Import CSV' en haut de la liste.")
        return response

    export_template_csv.short_description = "📥 Télécharger template CSV"

    # URL personnalisée pour l'import
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv),
                 name='saisie_equipes_club_import_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        """Import CSV des clubs"""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')

            if not csv_file:
                self.message_user(request, "❌ Aucun fichier sélectionné.", level=messages.ERROR)
                return render(request, 'admin/saisie_equipes/club/import_csv.html')

            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "❌ Le fichier doit être au format CSV.", level=messages.ERROR)
                return render(request, 'admin/saisie_equipes/club/import_csv.html')

            try:
                # Lire et décoder le fichier CSV
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)

                # Vérifier les colonnes
                if 'nom_club' not in reader.fieldnames:
                    self.message_user(request, "❌ La colonne 'nom_club' est manquante dans le CSV.", level=messages.ERROR)
                    return render(request, 'admin/saisie_equipes/club/import_csv.html')

                # Compteurs
                nb_nouveaux = 0
                nb_existants = 0
                erreurs = []

                # Traiter chaque ligne
                for numero_ligne, row in enumerate(reader, start=2):  # start=2 car ligne 1 = headers
                    try:
                        nom_club = row['nom_club'].strip()

                        if not nom_club:
                            erreurs.append(f"Ligne {numero_ligne}: Nom de club vide")
                            continue

                        # Créer le club s'il n'existe pas déjà
                        club, created = Club.objects.get_or_create(nom=nom_club)

                        if created:
                            nb_nouveaux += 1
                        else:
                            nb_existants += 1

                    except Exception as e:
                        erreurs.append(f"Ligne {numero_ligne}: {str(e)}")

                # Messages de résultat
                if nb_nouveaux > 0:
                    self.message_user(request, f"✅ {nb_nouveaux} nouveau(x) club(s) ajouté(s) avec succès.")

                if nb_existants > 0:
                    self.message_user(request, f"ℹ️ {nb_existants} club(s) étai(en)t déjà existant(s).")

                if erreurs:
                    self.message_user(request, f"⚠️ {len(erreurs)} erreur(s) détectée(s):", level=messages.WARNING)
                    for erreur in erreurs[:5]:  # Limiter à 5 erreurs affichées
                        self.message_user(request, f"• {erreur}", level=messages.ERROR)
                    if len(erreurs) > 5:
                        self.message_user(request, f"... et {len(erreurs) - 5} autres erreurs.", level=messages.ERROR)

                # Rediriger vers la liste des clubs si tout s'est bien passé
                if len(erreurs) == 0:
                    return redirect('..')

            except Exception as e:
                self.message_user(request, f"❌ Erreur lors de la lecture du fichier CSV: {str(e)}", level=messages.ERROR)

        # Afficher le formulaire d'import
        return render(request, 'admin/saisie_equipes/club/import_csv.html', {
            'title': 'Import des clubs par CSV',
            'opts': self.model._meta,
            'has_view_permission': True,
        })

    def changelist_view(self, request, extra_context=None):
        """Ajoute un lien Import CSV dans la vue liste"""
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'import-csv/'
        return super().changelist_view(request, extra_context)