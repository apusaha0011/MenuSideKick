from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow only admins to edit objects,
    but read-only access (GET, HEAD, OPTIONS) for authenticated users.
    """

    def has_permission(self, request, view):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
        if request.method in SAFE_METHODS:
            # Allow any authenticated user to read
            return request.user and request.user.is_authenticated
        # Only admin (staff or superuser) can write
        return request.user and request.user.is_staff


class IsSelfOrAdmin(BasePermission):
    """
    Custom permission to allow users to edit their own objects, admin can edit any object.
    Works for both User objects and related objects that have a 'user' attribute (e.g. Profile).
    """

    def has_object_permission(self, request, view, obj):
        # allow admins/staff
        if request.user and request.user.is_staff:
            return True

        # If the object has a related 'user' attribute (e.g. Profile), compare that
        if hasattr(obj, "user"):
            return obj.user == request.user

        # Fallback for User objects or direct comparisons
        return obj == request.user
