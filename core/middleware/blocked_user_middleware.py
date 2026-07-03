# apps/users/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework import status


class BlockedUserMiddleware(MiddlewareMixin):
    """
    Blocks requests from users who have is_blocked=True.
    
    Why this works:
    - Runs on EVERY request after authentication
    - Blocks both new logins and existing sessions/tokens
    - Simple: Just one check, one place to maintain
    """
    
    def process_request(self, request):
        # Skip for unauthenticated users (let them reach login endpoint)
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Check if authenticated user is blocked
        if request.user.is_blocked:
            return JsonResponse(
                {
                    "detail": "Your account has been blocked. Please contact support.",
                    "error_code": "ACCOUNT_BLOCKED"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # User is not blocked, continue normally
        return None