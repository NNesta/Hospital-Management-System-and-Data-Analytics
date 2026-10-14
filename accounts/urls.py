from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # POST only (Django 5)
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/password/", views.PasswordChangeView.as_view(), name="password_change"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/new/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", views.UserDeactivateView.as_view(), name="user_delete"),
    path("users/<int:pk>/password/", views.UserSetPasswordView.as_view(), name="user_password"),
]
