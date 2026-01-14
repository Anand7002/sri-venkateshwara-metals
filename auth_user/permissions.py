from rest_framework.permissions import BasePermission, SAFE_METHODS


def _user_role(user):
    if not user or not user.is_authenticated:
        return None
    if hasattr(user, 'userrole'):
        return user.userrole.role
    return 'cashier'


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return _user_role(request.user) == 'admin'


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        role = _user_role(request.user)
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated and role in {'admin', 'cashier'}
        return role == 'admin'


class IsAdminOrCashier(BasePermission):
    def has_permission(self, request, view):
        return _user_role(request.user) in {'admin', 'cashier'}

