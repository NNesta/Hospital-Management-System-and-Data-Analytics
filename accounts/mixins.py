"""Role-based access control shared by every app.

Views declare who may use them; hiding a button in a template is only cosmetic.

    class PatientCreateView(RoleRequiredMixin, CreateView):
        allowed_roles = [Role.ADMIN, Role.RECEPTIONIST]

    @role_required(Role.PHARMACIST)
    def dispense(request, pk): ...
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles: list[str] = []

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles


def role_required(*roles):
    """Function-view twin of RoleRequiredMixin: 403 unless the user has a role."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not (request.user.is_authenticated and request.user.role in roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


class ProtectedDeleteMixin:
    """For DeleteViews: flash a success alert, and turn a PROTECT foreign-key
    error into a friendly alert instead of a crash page."""

    protected_message = "This record cannot be deleted because other records depend on it."

    def form_valid(self, form):
        label = str(self.object)
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return redirect(self.object.get_absolute_url())
        messages.success(self.request, f"{label} was deleted.")
        return response


class SearchMixin:
    """Filter a ListView with ?q= across `search_fields` (icontains)."""

    search_fields: list[str] = []

    def get_search_query(self):
        return self.request.GET.get("q", "").strip()

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.get_search_query()
        if query and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(condition)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.get_search_query()
        return context


class StatusGuardMixin:
    """Only allow GET/POST while `is_editable(obj)` is true, e.g. a prescription
    that is still Pending. Runs after RoleRequiredMixin's permission check."""

    locked_message = "This record can no longer be changed."

    def is_editable(self, obj):
        return True

    def _guard(self, request):
        obj = self.get_object()
        if not self.is_editable(obj):
            messages.error(request, self.locked_message)
            return redirect(obj)
        return None

    def get(self, request, *args, **kwargs):
        return self._guard(request) or super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._guard(request) or super().post(request, *args, **kwargs)
