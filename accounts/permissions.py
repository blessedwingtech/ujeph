# accounts/permissions.py
from django.contrib import messages
from django.shortcuts import redirect

def is_django_superuser(user):
    """Vérifie si l'utilisateur est un superuser Django"""
    return user.is_authenticated and user.is_superuser

def django_superuser_required(view_func):
    """Décorateur pour restreindre aux superusers Django"""
    def wrapper(request, *args, **kwargs):
        if not is_django_superuser(request.user):
            messages.error(request, "❌ Accès réservé au super administrateur système.")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper