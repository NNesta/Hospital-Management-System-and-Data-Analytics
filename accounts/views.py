from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import AdminSetPasswordForm, LoginForm, OwnPasswordChangeForm, UserCreateForm, UserUpdateForm
from .mixins import RoleRequiredMixin, SearchMixin
from .models import Role, User


class LoginView(auth_views.LoginView):
    """AdminLTE login page. Django already marks LoginView @login_not_required."""

    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class ProfileView(TemplateView):
    template_name = "accounts/profile.html"


class PasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = OwnPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password was changed."


# --- User management (Admin only) ---------------------------------------------------


class UserListView(RoleRequiredMixin, SearchMixin, ListView):
    allowed_roles = [Role.ADMIN]
    model = User
    paginate_by = 10
    search_fields = ["username", "first_name", "last_name", "email", "phone"]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.GET.get("role")
        if role in Role.values:
            queryset = queryset.filter(role=role)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_choices"] = Role.choices
        context["selected_role"] = self.request.GET.get("role", "")
        return context


class UserCreateView(RoleRequiredMixin, SuccessMessageMixin, CreateView):
    allowed_roles = [Role.ADMIN]
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_message = "User %(username)s was created."


class UserDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [Role.ADMIN]
    model = User
    context_object_name = "account"  # `user` is the logged-in user in templates


class UserUpdateView(RoleRequiredMixin, SuccessMessageMixin, UpdateView):
    allowed_roles = [Role.ADMIN]
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    context_object_name = "account"
    success_message = "User %(username)s was updated."


class UserDeactivateView(RoleRequiredMixin, DetailView):
    """'Delete' for users: keep the row for history, just block the login."""

    allowed_roles = [Role.ADMIN]
    model = User
    template_name = "accounts/user_confirm_delete.html"
    context_object_name = "account"

    def post(self, request, *args, **kwargs):
        account = self.get_object()
        if account == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            account.is_active = False
            account.save(update_fields=["is_active"])
            messages.success(request, f"{account} was deactivated and can no longer sign in.")
        return redirect("accounts:user_list")


class UserSetPasswordView(RoleRequiredMixin, FormView):
    allowed_roles = [Role.ADMIN]
    form_class = AdminSetPasswordForm
    template_name = "accounts/user_password.html"

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(User, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account"] = self.account
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f"Password for {self.account} was reset.")
        return redirect(reverse("accounts:user_detail", args=[self.account.pk]))
