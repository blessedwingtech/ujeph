# accounts/middleware.py
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
import datetime

class AutoLogoutMiddleware:
    """Middleware pour déconnecter automatiquement après période d'inactivité"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = 300  # 5 minutes en secondes
    
    def __call__(self, request):
        # Si l'utilisateur est authentifié
        if request.user.is_authenticated:
            current_time = timezone.now()
            
            # Vérifier la dernière activité
            last_activity_str = request.session.get('last_activity')
            
            if last_activity_str:
                try:
                    last_activity = datetime.datetime.fromisoformat(last_activity_str)
                    time_diff = (current_time - last_activity).total_seconds()
                    
                    # Si le temps d'inactivité dépasse le timeout
                    if time_diff > self.timeout:
                        # Audit de la déconnexion
                        if hasattr(request.user, 'username'):
                            from .audit_utils import audit_logout
                            audit_logout(request, request.user)
                        
                        logout(request)
                        request.session.flush()
                        
                        # Rediriger avec message
                        messages.warning(request, "Vous avez été déconnecté automatiquement après 5 minutes d'inactivité.")
                        return redirect('accounts:login')
                
                except (ValueError, TypeError):
                    pass
            
            # Mettre à jour le timestamp de dernière activité
            request.session['last_activity'] = current_time.isoformat()
        
        response = self.get_response(request)
        return response


def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
