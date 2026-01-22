from django.urls import path
from .views import  accueil_view, declaration_view, confirmation_view, consultation_view, consultation_passee_view, candidature_liste_view, mes_candidatures_view, candidature_form_view # non de la def dans views.py,

urlpatterns = [
    path("", accueil_view, name="accueil"),  # Page d'accueil
    path("declaration/", declaration_view, name="declaration"),
    path("confirmation/", confirmation_view, name="confirmation"),
    path("consultation/", consultation_view, name="consultation"),
    path("consultation-archive/", consultation_passee_view, name="consultation_archive"),
    path("candidature/", candidature_liste_view, name="candidature_liste"),
    path("candidature/<int:tournoi_id>/", candidature_form_view, name="candidature_form"),
    path("candidature/mes-candidatures/", mes_candidatures_view, name="mes_candidatures"),
]
