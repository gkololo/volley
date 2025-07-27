import datetime
from django.db import models
from django.core.validators import MaxValueValidator, EmailValidator



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

class Club(models.Model):
    nom = models.CharField(max_length=300)


    def __str__(self):
        return self.nom

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
    default=Zone.AUCUNE,  # valeur par défaut explicite
    blank=True,
    verbose_name="Zone géographique si applicable"
)
    nombre_equipes = models.PositiveSmallIntegerField(
    "Nombre d'équipes",
    validators=[MaxValueValidator(10)]
)
    date_tournoi= models.DateField("Date du tournoi", default=datetime.date.today)
    remarques = models.TextField(blank=True)
    declarant= models.CharField(max_length=200, default="inconnu")
    email_club= models.EmailField(validators=[EmailValidator(message="Email non valide")], default="inconnu@exemple.com")
    date_declaration = models.DateTimeField("Date de déclaration", auto_now_add=True)


    def __str__(self):
        return f"{self.declarant} ({self.club}) - {self.nombre_equipes} équipe(s) - {self.get_categorie_age_display()} {self.get_sexe_display()} {self.get_zone_display()}"



