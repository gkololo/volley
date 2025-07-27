from django.contrib import admin
from .models import Declaration, CategorieAge, Sexe, Zone, Club

# Register your models here.
@admin.register(Declaration)
class DeclarationAdmin(admin.ModelAdmin):
    list_display = ("club", "declarant", "nombre_equipes", "categorie_age", "sexe", "zone", "date_tournoi")

admin.site.register(Club)