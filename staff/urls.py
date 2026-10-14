from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("departments/", views.DepartmentListView.as_view(), name="department_list"),
    path("departments/new/", views.DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/", views.DepartmentDetailView.as_view(), name="department_detail"),
    path("departments/<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="department_update"),
    path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),
    path("doctors/", views.DoctorListView.as_view(), name="doctor_list"),
    path("doctors/new/", views.DoctorCreateView.as_view(), name="doctor_create"),
    path("doctors/<int:pk>/", views.DoctorDetailView.as_view(), name="doctor_detail"),
    path("doctors/<int:pk>/edit/", views.DoctorUpdateView.as_view(), name="doctor_update"),
    path("doctors/<int:pk>/delete/", views.DoctorDeleteView.as_view(), name="doctor_delete"),
]
