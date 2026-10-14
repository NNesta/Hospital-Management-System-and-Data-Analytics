from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.AppointmentListView.as_view(), name="list"),
    path("new/", views.AppointmentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AppointmentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.AppointmentUpdateView.as_view(), name="update"),
    path("<int:pk>/complete/", views.appointment_complete, name="complete"),
    path("<int:pk>/cancel/", views.appointment_cancel, name="cancel"),
    path("<int:pk>/no-show/", views.appointment_no_show, name="no_show"),
    path("records/", views.MedicalRecordListView.as_view(), name="record_list"),
    path("records/<int:pk>/", views.MedicalRecordDetailView.as_view(), name="record_detail"),
    path("records/<int:pk>/edit/", views.MedicalRecordUpdateView.as_view(), name="record_update"),
    path("records/<int:pk>/delete/", views.MedicalRecordDeleteView.as_view(), name="record_delete"),
]
