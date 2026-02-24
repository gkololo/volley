import datetime
from django.db import models
from django.core.validators import MaxValueValidator, EmailValidator
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Sexe(models.TextChoices):
    MASCULIN = "M", "Masculin"
    FEMININ = "F", "Féminin"

class CategorieAge(models.TextChoices):
    M11 = "M11", "Moins de 11 ans"
    M13 = "M13", "Moins de 13 ans"
    M15 = "M15", "Moins de 15 ans"
    M18 = "M18", "Moins de 18 ans"

class Zone(models.TextChoices):
    NORD = "N", "Zone Nord"
    SUD = "S", "Zone Sud"
    AUCUNE = "", "Pas de zone"

class Poule(models.TextChoices):
    """Choix de poule pour une équipe"""
    HAUTE = "HAUTE", "Poule Haute"
    BASSE = "BASSE", "Poule Basse"
    UNIQUE = "UNIQUE", "Poule Unique"
    # Vide = pas de poule (pour tournois sans poules)

class StatutTournoi(models.TextChoices):
    """Statut d'un tournoi"""
    PLANIFIE = "PLANIFIE", "Planifié"
    CONFIRME = "CONFIRME", "Confirmé"
    ANNULE = "ANNULE", "Annulé"
    TERMINE = "TERMINE", "Terminé"

class StatutCandidature(models.TextChoices):
    """Statut d'une candidature à l'organisation"""
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    VALIDEE = "VALIDEE", "Validée"
    REFUSEE = "REFUSEE", "Refusée"
    RETIREE = "RETIREE", "Retirée"

class Club(models.Model):
    nom = models.CharField(max_length=300)

    def __str__(self):
        return self.nom

class Tournoi(models.Model):
    """
    Tournoi officiel créé par le staff
    Un tournoi = 1 date + 1 catégorie + 1 sexe (+ optionnel zone)
    """

    titre = models.CharField(
        "Titre du tournoi",
        max_length=100,
        blank=True,
        help_text="Ex: 'Journée 2', 'FINALITÉ'"
        )

    date = models.DateField(
        "Date du tournoi",
        help_text="Date à laquelle le tournoi aura lieu"
    )

    categorie_age = models.CharField(
        "Catégorie d'âge",
        max_length=3,
        choices=CategorieAge.choices,
        help_text="Ex: M11, M13, M15, M18"
    )

    sexe = models.CharField(
        "Sexe",
        max_length=1,
        choices=Sexe.choices,
        help_text="Masculin ou Féminin"
    )

    zone = models.CharField(
        "Zone géographique",
        max_length=1,
        choices=Zone.choices,
        blank=True,
        help_text="Nord, Sud, ou vide si pas de zone"
    )

    club_organisateur = models.ForeignKey(
        'Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tournois_organises',
        verbose_name="Club organisateur",
        help_text="Club responsable de l'organisation (défini après validation candidature)"
    )

    lieu = models.CharField(
        "Lieu / Gymnase",
        max_length=200,
        blank=True,
        help_text="Nom du gymnase (défini après validation candidature)"
    )
    # 🆕 NOUVEAU : Poules disponibles pour ce tournoi
    poules_disponibles = models.JSONField(
        "Poules disponibles",
        default=list,
        blank=True,
        help_text="Liste des poules disponibles pour ce tournoi (ex: ['HAUTE', 'BASSE'] ou ['UNIQUE'])"
    )

    statut = models.CharField(
        "Statut",
        max_length=20,
        choices=StatutTournoi.choices,
        default=StatutTournoi.PLANIFIE,
        help_text="État actuel du tournoi"
    )

    est_publie = models.BooleanField(
        "Publié",
        default=True,
        help_text="Si False, seul le staff voit le tournoi"
    )

    remarques = models.TextField(
        "Remarques internes",
        blank=True,
        help_text="Notes du staff (non visibles publiquement)"
    )

    created_at = models.DateTimeField(
        "Créé le",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        "Modifié le",
        auto_now=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tournois_crees',
        verbose_name="Créé par",
        help_text="Membre du staff qui a créé le tournoi"
    )

    def __str__(self):
        """Représentation textuelle"""
        zone_str = f" {self.get_zone_display()}" if self.zone else ""
        org_str = f" - Org: {self.club_organisateur.nom}" if self.club_organisateur else ""

        return (
            f"{self.date.strftime('%d/%m/%Y')} - "
            f"{self.get_categorie_age_display()} "
            f"{self.get_sexe_display()}"
            f"{zone_str}"
            f"{org_str}"
        )

    def get_nb_declarations(self):
        """Nombre de clubs qui ont déclaré des équipes"""
        return self.declarations.count()

    def get_nb_equipes_total(self):
        """Nombre total d'équipes inscrites"""
        from django.db.models import Sum
        total = self.declarations.aggregate(
            total=Sum('nombre_equipes')
        )['total']
        return total or 0

    def get_nb_candidatures(self):
        """Nombre de clubs qui ont candidaté pour organiser"""
        return self.candidatures.count()

    def get_candidatures_en_attente(self):
        """Candidatures qui attendent traitement"""
        return self.candidatures.filter(statut=StatutCandidature.EN_ATTENTE)

    def a_organisateur(self):
        """Vérifie si un organisateur a été choisi"""
        return self.club_organisateur is not None

    def est_passe(self):
        """Vérifie si le tournoi est dans le passé"""
        return self.date < timezone.now().date()

    def peut_recevoir_declarations(self):
        """Vérifie si on peut encore déclarer des équipes"""
        return (
            self.est_publie and
            self.statut in [StatutTournoi.PLANIFIE, StatutTournoi.CONFIRME] and
            not self.est_passe()
        )

    def peut_recevoir_candidatures(self):
        """Vérifie si on peut encore candidater pour organiser"""
        return (
            self.est_publie and
            self.statut in [StatutTournoi.PLANIFIE, StatutTournoi.CONFIRME] and
            not self.est_passe()
        )

    class Meta:
        verbose_name = "Tournoi"
        verbose_name_plural = "Tournois"
        ordering = ['date', 'categorie_age', 'sexe']
        unique_together = [['date', 'categorie_age', 'sexe', 'zone']]
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['statut']),
            models.Index(fields=['date', 'statut']),
        ]

class Candidature(models.Model):
    """
    Candidature d'un club pour ORGANISER un tournoi
    """

    tournoi = models.ForeignKey(
        'Tournoi',
        on_delete=models.CASCADE,
        related_name='candidatures',
        verbose_name="Tournoi"
    )

    club = models.ForeignKey(
        'Club',
        on_delete=models.CASCADE,
        related_name='candidatures',
        verbose_name="Club candidat"
    )

    declarant = models.CharField(
        "Personne de contact",
        max_length=200,
        help_text="Nom et prénom de la personne qui dépose la candidature"
    )

    email_contact = models.EmailField(
        "Email de contact",
        validators=[EmailValidator(message="Email non valide")],
        help_text="Email pour les notifications"
    )

    telephone_contact = models.CharField(
        "Téléphone",
        max_length=20,
        blank=True,
        help_text="Numéro de téléphone (optionnel)"
    )

    lieu = models.CharField(
        "Lieu proposé",
        max_length=200,
        help_text="Nom du gymnase où le club propose d'organiser"
    )

    remarques = models.TextField(
        "Remarques / Motivations",
        blank=True,
        help_text="Commentaires du club sur sa candidature"
    )

    statut = models.CharField(
        "Statut",
        max_length=20,
        choices=StatutCandidature.choices,
        default=StatutCandidature.EN_ATTENTE,
        help_text="État de traitement de la candidature"
    )

    raison_refus = models.TextField(
        "Raison du refus",
        blank=True,
        help_text="Si refusée, explication donnée au club"
    )

    traite_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidatures_traitees',
        verbose_name="Traité par",
        help_text="Membre du staff qui a validé/refusé"
    )

    date_traitement = models.DateTimeField(
        "Date de traitement",
        null=True,
        blank=True,
        help_text="Quand la candidature a été validée/refusée"
    )

    created_at = models.DateTimeField(
        "Créée le",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        "Modifiée le",
        auto_now=True
    )

    def __str__(self):
        return (
            f"Candidature {self.club.nom} - "
            f"{self.tournoi} - "
            f"{self.get_statut_display()}"
        )

    def peut_etre_modifiee(self):
        """Vérifie si la candidature peut encore être modifiée"""
        return self.statut == StatutCandidature.EN_ATTENTE

    def peut_etre_retiree(self):
        """Vérifie si le club peut retirer sa candidature"""
        return self.statut in [
            StatutCandidature.EN_ATTENTE,
            StatutCandidature.VALIDEE
        ]

    def valider(self, user):
        """
        Valide la candidature et met à jour le tournoi

        Actions :
        1. Change statut → VALIDEE
        2. Met à jour tournoi.club_organisateur
        3. Met à jour tournoi.lieu
        4. Change tournoi.statut → CONFIRME

        Args:
            user: Utilisateur staff qui valide
        """
        self.statut = StatutCandidature.VALIDEE
        self.traite_par = user
        self.date_traitement = timezone.now()
        self.save()

        # Mettre à jour le tournoi
        self.tournoi.club_organisateur = self.club
        self.tournoi.lieu = self.lieu
        self.tournoi.statut = StatutTournoi.CONFIRME
        self.tournoi.save()

    def refuser(self, user, raison):
        """
        Refuse la candidature

        Args:
            user: Utilisateur staff qui refuse
            raison: Motif du refus
        """
        self.statut = StatutCandidature.REFUSEE
        self.raison_refus = raison
        self.traite_par = user
        self.date_traitement = timezone.now()
        self.save()

    def retirer(self):
        """
        Le club retire sa candidature

        Si la candidature était validée, il faut aussi
        retirer l'organisateur du tournoi
        """
        ancien_statut = self.statut

        self.statut = StatutCandidature.RETIREE
        self.save()

        # Si c'était la candidature validée, vider le tournoi
        if ancien_statut == StatutCandidature.VALIDEE:
            self.tournoi.club_organisateur = None
            self.tournoi.lieu = ""
            self.tournoi.statut = StatutTournoi.PLANIFIE
            self.tournoi.save()

    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        ordering = ['-created_at']
        unique_together = [['tournoi', 'club']]
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['tournoi', 'statut']),
            models.Index(fields=['club', 'statut']),
        ]

class Declaration(models.Model):
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        verbose_name="Club affilié"
    )
    categorie_age = models.CharField(
        max_length=3,
        choices=CategorieAge.choices,
        default=CategorieAge.M11,
        verbose_name="Catégorie d'âge"
    )
    sexe = models.CharField(
        max_length=1,
        choices=Sexe.choices,
        default=Sexe.MASCULIN,
        verbose_name="Sexe"
    )
    zone = models.CharField(
        max_length=1,
        choices=Zone.choices,
        default=Zone.AUCUNE,
        blank=True,
        verbose_name="Zone géographique si applicable"
    )
    nombre_equipes = models.PositiveSmallIntegerField(
        "Nombre d'équipes",
        validators=[MaxValueValidator(10)]
    )

    # 🆕 NOUVEAU : Noms des équipes
    noms_equipes = models.JSONField(
        "Noms des équipes",
        default=list,
        blank=True,
        help_text="Liste des noms d'équipes (ex: ['TGV A', 'TGV B'])"
    )
    # 🆕 NOUVEAU : Poules des équipes
    poules_equipes = models.JSONField(
        "Poules des équipes",
        default=list,
        blank=True,
        help_text="Liste des poules assignées à chaque équipe (ex: ['HAUTE', 'BASSE', ''])"
    )
    # ⚠️ GARDER TEMPORAIREMENT pour migration
    date_tournoi = models.DateField("Date du tournoi", default=datetime.date.today)

    # 🆕 NOUVEAU CHAMP
    tournoi = models.ForeignKey(
        'Tournoi',
        on_delete=models.CASCADE,
        null=True,  # ⚠️ Important pour migration !
        blank=True,
        related_name='declarations',
        verbose_name="Tournoi",
        help_text="Tournoi pour lequel l'équipe est déclarée"
    )

    remarques = models.TextField(blank=True)

    declarant = models.CharField(
        "Déclarant",
        max_length=200,
    )
    email_club = models.EmailField(
        "Email du club",
        validators=[EmailValidator(message="Email non valide")],
    )

    date_declaration = models.DateTimeField("Date de déclaration", auto_now_add=True)

    def __str__(self):
        equipes_str = ", ".join(self.noms_equipes) if self.noms_equipes else f"{self.nombre_equipes} équipe(s)"
        return f"{self.declarant} ({self.club}) - {equipes_str} - {self.get_categorie_age_display()} {self.get_sexe_display()} {self.get_zone_display()}"

    def get_noms_equipes_formatte(self):
        """Retourne les noms d'équipes formatés pour affichage"""
        if self.noms_equipes:
            return ", ".join(self.noms_equipes)
        return f"{self.nombre_equipes} équipe(s)"

    def get_equipes_avec_poules(self):
        """Retourne les équipes avec leurs poules formatées pour affichage"""
        if not self.noms_equipes:
            return []

        equipes = []
        for i, nom in enumerate(self.noms_equipes):
            poule = ""
            if self.poules_equipes and i < len(self.poules_equipes):
                poule = self.poules_equipes[i] or ""

            equipes.append({
                'nom': nom,
                'poule': poule,
                'poule_display': dict(Poule.choices).get(poule, "Aucune") if poule else "Aucune"
            })

        return equipes

    def get_equipes_par_poule(self):
        """Retourne les équipes groupées par poule"""
        if not self.noms_equipes:
            return {}

        equipes_par_poule = {}
        for i, nom in enumerate(self.noms_equipes):
            poule = self.poules_equipes[i] if i < len(self.poules_equipes) and self.poules_equipes[i] else "AUCUNE"

            if poule not in equipes_par_poule:
                equipes_par_poule[poule] = []

            equipes_par_poule[poule].append(nom)

        return equipes_par_poule

    class Meta:
        verbose_name = "Déclaration"
        verbose_name_plural = "Déclarations"
        ordering = ['-date_declaration']