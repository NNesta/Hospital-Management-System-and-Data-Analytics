from django.urls import path

from . import views

app_name = "pharmacy"

urlpatterns = [
    path("medicines/", views.MedicineListView.as_view(), name="medicine_list"),
    path("medicines/new/", views.MedicineCreateView.as_view(), name="medicine_create"),
    path("medicines/<int:pk>/", views.MedicineDetailView.as_view(), name="medicine_detail"),
    path("medicines/<int:pk>/edit/", views.MedicineUpdateView.as_view(), name="medicine_update"),
    path("medicines/<int:pk>/delete/", views.MedicineDeleteView.as_view(), name="medicine_delete"),
    path("prescriptions/", views.PrescriptionListView.as_view(), name="prescription_list"),
    path("prescriptions/new/<int:record_pk>/", views.PrescriptionCreateView.as_view(), name="prescription_create"),
    path("prescriptions/<int:pk>/", views.PrescriptionDetailView.as_view(), name="prescription_detail"),
    path("prescriptions/<int:pk>/edit/", views.PrescriptionUpdateView.as_view(), name="prescription_update"),
    path("prescriptions/<int:pk>/delete/", views.PrescriptionDeleteView.as_view(), name="prescription_delete"),
    path("prescriptions/<int:pk>/dispense/", views.prescription_dispense, name="dispense"),
]
