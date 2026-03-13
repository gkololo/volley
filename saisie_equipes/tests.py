"""
═══════════════════════════════════════════════════
🧪 TESTS AUTOMATISÉS — VolleyChamp
Sprint 4 — Tests basiques
═══════════════════════════════════════════════════

Lancer avec : python manage.py test saisie_equipes

Groupes :
  1. TournoiModelTests      — règles métier du modèle Tournoi
  2. CandidatureModelTests  — règles métier du modèle Candidature
  3. VuesPubliquesTests     — pages accessibles à tous
  4. VuesStaffTests         — sécurité accès staff
"""

from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import (
    Club, Tournoi, Declaration, Candidature,
    Sexe, CategorieAge, StatutTournoi, StatutCandidature
)


# ═══════════════════════════════════════════════════
# 🔧 HELPER — fabrique un tournoi rapidement
# ═══════════════════════════════════════════════════

def creer_tournoi(date_tournoi=None, statut=StatutTournoi.PLANIFIE,
                  est_publie=True, **kwargs):
    """Crée un tournoi de test avec des valeurs par défaut raisonnables."""
    if date_tournoi is None:
        date_tournoi = timezone.now().date() + timedelta(days=30)
    return Tournoi.objects.create(
        date=date_tournoi,
        categorie_age=CategorieAge.M13,
        sexe=Sexe.MIXTE,
        statut=statut,
        est_publie=est_publie,
        **kwargs
    )


def creer_club(nom="Club Test"):
    return Club.objects.create(nom=nom)


# ═══════════════════════════════════════════════════
# GROUPE 1 — Modèle Tournoi
# ═══════════════════════════════════════════════════

class TournoiModelTests(TestCase):

    def test_tournoi_futur_peut_recevoir_declarations(self):
        """Un tournoi à venir et publié accepte les déclarations."""
        tournoi = creer_tournoi()
        self.assertTrue(tournoi.peut_recevoir_declarations())

    def test_tournoi_passe_ne_peut_pas_recevoir_declarations(self):
        """Un tournoi passé refuse les déclarations."""
        hier = timezone.now().date() - timedelta(days=1)
        tournoi = creer_tournoi(date_tournoi=hier)
        self.assertFalse(tournoi.peut_recevoir_declarations())

    def test_tournoi_annule_ne_peut_pas_recevoir_declarations(self):
        """Un tournoi annulé refuse les déclarations."""
        tournoi = creer_tournoi(statut=StatutTournoi.ANNULE)
        self.assertFalse(tournoi.peut_recevoir_declarations())

    def test_tournoi_non_publie_ne_peut_pas_recevoir_declarations(self):
        """Un tournoi non publié refuse les déclarations."""
        tournoi = creer_tournoi(est_publie=False)
        self.assertFalse(tournoi.peut_recevoir_declarations())

    def test_tournoi_futur_peut_recevoir_candidatures(self):
        """Un tournoi à venir et publié accepte les candidatures."""
        tournoi = creer_tournoi()
        self.assertTrue(tournoi.peut_recevoir_candidatures())

    def test_tournoi_passe_ne_peut_pas_recevoir_candidatures(self):
        """Un tournoi passé refuse les candidatures."""
        hier = timezone.now().date() - timedelta(days=1)
        tournoi = creer_tournoi(date_tournoi=hier)
        self.assertFalse(tournoi.peut_recevoir_candidatures())

    def test_sexe_mixte_affichage(self):
        """Sexe.MIXTE s'affiche correctement en français."""
        tournoi = creer_tournoi()
        self.assertEqual(tournoi.get_sexe_display(), "Féminin et Masculin")

    def test_sexe_default_est_mixte(self):
        """Le sexe par défaut d'un nouveau tournoi est MIXTE."""
        tournoi = Tournoi(
            date=timezone.now().date() + timedelta(days=10),
            categorie_age=CategorieAge.M15,
        )
        self.assertEqual(tournoi.sexe, Sexe.MIXTE)

    def test_get_nb_equipes_total_sans_declarations(self):
        """Un tournoi sans déclarations retourne 0 équipe."""
        tournoi = creer_tournoi()
        self.assertEqual(tournoi.get_nb_equipes_total(), 0)

    def test_get_nb_equipes_total_avec_declarations(self):
        """get_nb_equipes_total() additionne correctement les équipes."""
        tournoi = creer_tournoi()
        club = creer_club()
        Declaration.objects.create(
            tournoi=tournoi, club=club,
            nombre_equipes=3, declarant="Jean Dupont",
            email_club="jean@test.re"
        )
        Declaration.objects.create(
            tournoi=tournoi, club=creer_club("Club B"),
            nombre_equipes=2, declarant="Marie Martin",
            email_club="marie@test.re"
        )
        self.assertEqual(tournoi.get_nb_equipes_total(), 5)

    def test_a_organisateur_false_par_defaut(self):
        """Un nouveau tournoi n'a pas d'organisateur."""
        tournoi = creer_tournoi()
        self.assertFalse(tournoi.a_organisateur())

    def test_a_organisateur_true_apres_assignation(self):
        """a_organisateur() retourne True quand club_organisateur est défini."""
        club = creer_club()
        tournoi = creer_tournoi(club_organisateur=club)
        self.assertTrue(tournoi.a_organisateur())


# ═══════════════════════════════════════════════════
# GROUPE 2 — Modèle Candidature
# ═══════════════════════════════════════════════════

class CandidatureModelTests(TestCase):

    def setUp(self):
        """Prépare les objets réutilisés dans ce groupe."""
        self.club = creer_club("TGV Volley")
        self.tournoi = creer_tournoi()
        self.staff_user = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.candidature = Candidature.objects.create(
            tournoi=self.tournoi,
            club=self.club,
            declarant="Jean Dupont",
            email_contact="jean@tgv.re",
            lieu="Gymnase de Saint-Denis",
        )

    def test_candidature_statut_initial_en_attente(self):
        """Une nouvelle candidature est EN_ATTENTE par défaut."""
        self.assertEqual(self.candidature.statut, StatutCandidature.EN_ATTENTE)

    def test_valider_candidature_met_a_jour_statut(self):
        """Valider une candidature change son statut en VALIDEE."""
        self.candidature.valider(self.staff_user)
        self.assertEqual(self.candidature.statut, StatutCandidature.VALIDEE)

    def test_valider_candidature_assigne_organisateur_tournoi(self):
        """Valider une candidature assigne le club comme organisateur du tournoi."""
        self.candidature.valider(self.staff_user)
        self.tournoi.refresh_from_db()
        self.assertEqual(self.tournoi.club_organisateur, self.club)

    def test_valider_candidature_confirme_le_tournoi(self):
        """Valider une candidature passe le tournoi en statut CONFIRME."""
        self.candidature.valider(self.staff_user)
        self.tournoi.refresh_from_db()
        self.assertEqual(self.tournoi.statut, StatutTournoi.CONFIRME)

    def test_refuser_candidature_met_a_jour_statut(self):
        """Refuser une candidature change son statut en REFUSEE."""
        self.candidature.refuser(self.staff_user, "Gymnase non disponible")
        self.assertEqual(self.candidature.statut, StatutCandidature.REFUSEE)

    def test_refuser_candidature_enregistre_la_raison(self):
        """La raison de refus est bien enregistrée."""
        raison = "Gymnase non disponible ce jour-là"
        self.candidature.refuser(self.staff_user, raison)
        self.assertEqual(self.candidature.raison_refus, raison)


# ═══════════════════════════════════════════════════
# GROUPE 3 — Vues publiques
# ═══════════════════════════════════════════════════

class VuesPubliquesTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_accueil_retourne_200(self):
        response = self.client.get(reverse('accueil'))
        self.assertEqual(response.status_code, 200)

    def test_declaration_retourne_200(self):
        response = self.client.get(reverse('declaration'))
        self.assertEqual(response.status_code, 200)

    def test_consultation_retourne_200(self):
        response = self.client.get(reverse('consultation'))
        self.assertEqual(response.status_code, 200)

    def test_candidature_liste_retourne_200(self):
        response = self.client.get(reverse('candidature_liste'))
        self.assertEqual(response.status_code, 200)

    def test_mes_candidatures_retourne_200(self):
        response = self.client.get(reverse('mes_candidatures'))
        self.assertEqual(response.status_code, 200)


# ═══════════════════════════════════════════════════
# GROUPE 4 — Sécurité vues staff
# ═══════════════════════════════════════════════════

class VuesStaffTests(TestCase):

    def setUp(self):
        self.client = Client()
        # Utilisateur normal (non staff)
        self.user_normal = User.objects.create_user(
            username="normal", password="pass", is_staff=False
        )
        # Utilisateur staff
        self.user_staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )

    def test_dashboard_anonyme_redirige_vers_login(self):
        """Un visiteur anonyme est redirigé depuis le dashboard staff."""
        response = self.client.get(reverse('staff:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_tournois_liste_anonyme_redirige_vers_login(self):
        """Un visiteur anonyme est redirigé depuis la liste des tournois staff."""
        response = self.client.get(reverse('staff:tournois_liste'))
        self.assertEqual(response.status_code, 302)

    def test_candidatures_liste_anonyme_redirige_vers_login(self):
        """Un visiteur anonyme est redirigé depuis la liste des candidatures staff."""
        response = self.client.get(reverse('staff:candidatures_liste'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_user_normal_bloque(self):
        """Un utilisateur non staff ne peut pas accéder au dashboard."""
        self.client.login(username='normal', password='pass')
        response = self.client.get(reverse('staff:dashboard'))
        # Doit être redirigé (302) ou interdit (403)
        self.assertIn(response.status_code, [302, 403])

    def test_dashboard_staff_autorise(self):
        """Un utilisateur staff peut accéder au dashboard."""
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('staff:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_tournois_liste_staff_autorise(self):
        """Un utilisateur staff peut accéder à la liste des tournois."""
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('staff:tournois_liste'))
        self.assertEqual(response.status_code, 200)
