from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def staff_or_superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "⚠️ Connexion requise.")
            return redirect('admin:login')

        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "🚫 Accès réservé au personnel.")
        return redirect('accueil')

    return wrapper