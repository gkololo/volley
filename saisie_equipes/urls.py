from django.urls import path
from .views import  accueil_view, declaration_view, confirmation_view, consultation_view, consultation_passee_view # non de la def dans views.py

urlpatterns = [
    path("", accueil_view, name="accueil"),  # Page d'accueil
    path("declaration/", declaration_view, name="declaration"),
    path("confirmation/", confirmation_view, name="confirmation"),
    path("consultation/", consultation_view, name="consultation"),
    path("consultation-archive/", consultation_passee_view, name="consultation_archive"),
]
