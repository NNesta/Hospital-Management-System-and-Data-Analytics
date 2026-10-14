"""Root URLconf: it only includes each app's own URLconf."""

from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Ubuzima HMS administration"
admin.site.site_title = "Ubuzima HMS admin"
admin.site.index_title = "Backup data tools"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("analytics.urls")),  # dashboard at /
    path("accounts/", include("accounts.urls")),
    path("staff/", include("staff.urls")),
    path("patients/", include("patients.urls")),
    path("appointments/", include("appointments.urls")),
    path("pharmacy/", include("pharmacy.urls")),
    path("billing/", include("billing.urls")),
]
