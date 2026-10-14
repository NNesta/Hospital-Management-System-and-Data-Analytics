from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analytics/reports/", views.reports, name="reports"),
    path("analytics/reports/export/", views.export_csv, name="export_csv"),
]
