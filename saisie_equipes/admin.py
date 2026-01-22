import csv
import io
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from .models import Declaration, CategorieAge, Sexe, Zone, Club, Tournoi, Candidature

# ═══════════════════════════════════════════════════
# 🎨 PERSONNALISATION DU TITRE DE L'ADMIN
# ═══════════════════════════════════════════════════

admin.site.site_header = "Administration VolleyChamp"  # ← Titre en haut
admin.site.site_title = "VolleyChamp Admin"           # ← Titre de l'onglet navigateur
admin.site.index_title = "Gestion du championnat volley jeunes"     # ← Titre page d'accueil

# Register your models here.
@admin.register(Declaration)
class DeclarationAdmin(admin.ModelAdmin):
    list_display = (
        "club",
        "declarant",
        "nombre_equipes",
        "categorie_age",
        "sexe",
        "zone",
        "get_tournoi_display",  # ← NOUVEAU : Affiche le tournoi lié
        "date_tournoi"  # ← ANCIEN : À garder temporairement
    )
    list_filter = (
        "tournoi",  # ← NOUVEAU : Filtre par tournoi
        "categorie_age",
        "sexe",
        "zone",
        "date_tournoi"
    )
    search_fields = ("club__nom", "declarant", "tournoi__lieu")
    date_hierarchy = "date_tournoi"

    def get_tournoi_display(self, obj):
        """Affiche le tournoi avec un lien cliquable"""
        if obj.tournoi:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse("admin:saisie_equipes_tournoi_change", args=[obj.tournoi.pk])
            return format_html('<a href="{}">{}</a>', url, obj.tournoi)
        return "⚠️ Non lié"
    get_tournoi_display.short_description = "🏆 Tournoi"

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

# ═══════════════════════════════════════════════════
# 🏆 GESTION DES TOURNOIS
# ═══════════════════════════════════════════════════

class CandidatureInline(admin.TabularInline):
    """Affiche les candidatures directement dans la page du tournoi"""
    model = Candidature
    extra = 0  # Ne pas afficher de ligne vide pour nouvelle candidature
    can_delete = False  # Empêcher la suppression directe

    fields = (
        'club',
        'declarant',
        'lieu',
        'statut',
        'email_contact',
        'created_at'
    )
    readonly_fields = ('club', 'declarant', 'lieu', 'email_contact', 'created_at')

    def has_add_permission(self, request, obj=None):
        """Empêcher l'ajout de candidatures depuis cette inline"""
        return False

@admin.register(Tournoi)
class TournoiAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'categorie_age',
        'sexe',
        'zone',
        'club_organisateur',
        'lieu',
        'statut',
        'est_publie',
        'get_nb_declarations',
        'get_nb_equipes_total',
        'get_nb_candidatures_display'  # ← NOUVEAU
    )
    list_filter = (
        'statut',
        'est_publie',
        'categorie_age',
        'sexe',
        'zone',
        'date'
    )
    search_fields = (
        'club_organisateur__nom',
        'lieu'
    )
    date_hierarchy = 'date'

    # ← NOUVEAU : Inline pour voir les candidatures dans la page de détail
    inlines = [CandidatureInline]

    fieldsets = (
        ('📅 Informations du tournoi', {
            'fields': ('date', 'categorie_age', 'sexe', 'zone')
        }),
        ('🏢 Organisation', {
            'fields': ('club_organisateur', 'lieu', 'statut', 'est_publie')
        }),
        ('📝 Remarques', {
            'fields': ('remarques',),
            'classes': ('collapse',)
        }),
        ('ℹ️ Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_nb_declarations(self, obj):
        """Affiche le nombre de déclarations"""
        return obj.get_nb_declarations()
    get_nb_declarations.short_description = '🏐 Clubs'

    def get_nb_equipes_total(self, obj):
        """Affiche le nombre total d'équipes"""
        return obj.get_nb_equipes_total()
    get_nb_equipes_total.short_description = '👥 Équipes'

    def get_nb_candidatures_display(self, obj):
        """Affiche le nombre de candidatures avec détails"""
        from django.utils.html import format_html

        total = obj.candidatures.count()
        if total == 0:
            return "—"

        en_attente = obj.candidatures.filter(statut='EN_ATTENTE').count()
        validees = obj.candidatures.filter(statut='VALIDEE').count()
        refusees = obj.candidatures.filter(statut='REFUSEE').count()

        details = []
        if en_attente > 0:
            details.append(f'<span style="color: orange;">{en_attente} en attente</span>')
        if validees > 0:
            details.append(f'<span style="color: green;">{validees} validée(s)</span>')
        if refusees > 0:
            details.append(f'<span style="color: red;">{refusees} refusée(s)</span>')

        return format_html(f'<strong>{total}</strong> ({", ".join(details)})')

    get_nb_candidatures_display.short_description = '📋 Candidatures'

    def save_model(self, request, obj, form, change):
        """Enregistre le tournoi en ajoutant l'utilisateur créateur"""
        if not change:  # Si c'est une création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# ═══════════════════════════════════════════════════
# 📋 GESTION DES CANDIDATURES
# ═══════════════════════════════════════════════════

@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = (
        'tournoi',
        'club',
        'declarant',
        'lieu',
        'statut',
        'created_at',
        'traite_par'
    )
    list_filter = (
        'statut',
        'created_at',
        'date_traitement'
    )
    search_fields = (
        'club__nom',
        'declarant',
        'lieu',
        'email_contact'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('🏆 Tournoi', {
            'fields': ('tournoi',)
        }),
        ('🏢 Club candidat', {
            'fields': ('club', 'declarant', 'email_contact', 'telephone_contact')
        }),
        ('📍 Proposition', {
            'fields': ('lieu', 'remarques')
        }),
        ('✅ Traitement', {
            'fields': ('statut', 'raison_refus', 'traite_par', 'date_traitement')
        }),
        ('ℹ️ Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('created_at', 'updated_at', 'date_traitement', 'traite_par')

    actions = ['valider_candidatures', 'refuser_candidatures']

    def valider_candidatures(self, request, queryset):
        """Action pour valider des candidatures"""
        nb_validees = 0
        for candidature in queryset.filter(statut='EN_ATTENTE'):
            candidature.valider(request.user)
            nb_validees += 1

        self.message_user(
            request,
            f"✅ {nb_validees} candidature(s) validée(s) avec succès."
        )
    valider_candidatures.short_description = "✅ Valider les candidatures sélectionnées"

    def refuser_candidatures(self, request, queryset):
        """Action pour refuser des candidatures"""
        # Note : Pour une vraie utilisation, il faudrait un formulaire pour saisir la raison
        nb_refusees = 0
        for candidature in queryset.filter(statut='EN_ATTENTE'):
            candidature.refuser(request.user, "Refusé par action groupée")
            nb_refusees += 1

        self.message_user(
            request,
            f"❌ {nb_refusees} candidature(s) refusée(s)."
        )
    refuser_candidatures.short_description = "❌ Refuser les candidatures sélectionnées"