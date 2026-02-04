"""
═══════════════════════════════════════════════════
🔐 VUES D'AUTHENTIFICATION - VolleyChamp
═══════════════════════════════════════════════════

Vues pour login/logout personnalisées.
À créer comme fichier séparé : saisie_equipes/auth_views.py
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    """
    Vue de connexion personnalisée
    """
    # Si déjà connecté, rediriger
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('staff:dashboard')
        return redirect('accueil')
    
    # Récupérer l'URL de redirection
    next_url = request.GET.get('next') or request.POST.get('next', '')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, "❌ Veuillez renseigner identifiant et mot de passe.")
            return render(request, 'authentication/login.html', {'next': next_url})
        
        # Authentification
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Message de bienvenue
            nom = user.get_full_name() or user.username
            messages.success(request, f"✅ Bienvenue {nom} !")
            
            # Redirection
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            
            if user.is_staff or user.is_superuser:
                return redirect('staff:dashboard')
            
            return redirect('accueil')
        
        else:
            messages.error(request, "❌ Identifiant ou mot de passe incorrect.")
    
    return render(request, 'authentication/login.html', {'next': next_url})


def logout_view(request):
    """
    Vue de déconnexion
    """
    username = request.user.get_full_name() or request.user.username \
               if request.user.is_authenticated else None
    
    logout(request)
    
    if username:
        messages.success(request, f"👋 Au revoir {username} !")
    else:
        messages.success(request, "👋 Vous êtes déconnecté.")
    
    return redirect('accueil')
