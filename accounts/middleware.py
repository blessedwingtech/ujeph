# accounts/middleware.py
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import JsonResponse
import datetime

class AutoLogoutMiddleware:
    """
    Middleware de déconnexion automatique basé sur l'inactivité.
    - NE MET JAMAIS À JOUR last_activity
    - LIT uniquement la session
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.TIMEOUT = 300              # 5 minutes
        self.WARNING_THRESHOLD = 60     # warning à 60 secondes

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            last_activity_str = request.session.get('last_activity')

            if last_activity_str:
                try:
                    last_activity = datetime.datetime.fromisoformat(last_activity_str)
                    elapsed = (now - last_activity).total_seconds()

                    # 🔴 SESSION EXPIRÉE
                    if elapsed >= self.TIMEOUT:
                        logout(request)
                        request.session.flush()

                        # Requête AJAX
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'timeout': True}, status=401)

                        return redirect('accounts:login')

                    # 🔴 CALCUL DU TEMPS RESTANT
                    remaining = int(self.TIMEOUT - elapsed)
                    show_warning = remaining <= self.WARNING_THRESHOLD

                    request.session['remaining_time'] = remaining
                    request.session['show_warning'] = show_warning

                except Exception:
                    # Sécurité : reset propre
                    request.session['last_activity'] = now.isoformat()
                    request.session['remaining_time'] = self.TIMEOUT
                    request.session['show_warning'] = False

        response = self.get_response(request)

        # 🔴 HEADERS POUR JS
        if request.user.is_authenticated:
            response['X-Session-Remaining'] = str(
                request.session.get('remaining_time', self.TIMEOUT)
            )
            response['X-Session-Warning'] = 'true' if request.session.get('show_warning') else 'false'
            response['X-Session-Timeout'] = str(self.TIMEOUT)
            response['Access-Control-Expose-Headers'] = (
                'X-Session-Remaining, X-Session-Warning, X-Session-Timeout'
            )

        return response


def get_client_ip(request):
    """Retourne l'adresse IP réelle du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
