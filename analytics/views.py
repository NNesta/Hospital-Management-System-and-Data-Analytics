import csv

from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.mixins import role_required
from accounts.models import Role
from billing.models import InvoiceItem, Payment

from . import queries
from .forms import ReportFilterForm

# Section order per role: accountants see finance first, pharmacists stock first.
SECTION_ORDER = {
    Role.ACCOUNTANT: ["finance", "clinical", "pharmacy"],
    Role.PHARMACIST: ["pharmacy", "clinical", "finance"],
}
DEFAULT_SECTIONS = ["clinical", "finance", "pharmacy"]

KPI_ORDER = {
    Role.ACCOUNTANT: ["revenue", "outstanding", "patients", "appointments", "low_stock", "doctors"],
    Role.PHARMACIST: ["low_stock", "appointments", "patients", "doctors", "revenue", "outstanding"],
}
DEFAULT_KPIS = ["patients", "appointments", "revenue", "outstanding", "low_stock", "doctors"]

MONEY = DecimalField(max_digits=14, decimal_places=2)


def dashboard(request):
    """Role-aware KPI dashboard, computed live with the ORM."""
    user = request.user
    scope = queries.scope_for(user)
    numbers = queries.kpis(scope)
    is_doctor = user.role == Role.DOCTOR

    cards = {
        "patients": {
            "label": "My patients" if is_doctor else "Total patients",
            "value": numbers["total_patients"],
            "sub": f"+{numbers['new_patients_month']} new this month",
            "icon": "bi-people-fill",
            "color": "primary",
            "url": "patients:list",
        },
        "appointments": {
            "label": "Today's appointments",
            "value": numbers["today_total"],
            "sub": f"{numbers['today_scheduled']} scheduled · {numbers['today_completed']} completed",
            "icon": "bi-calendar2-check-fill",
            "color": "info",
            "url": "appointments:list",
        },
        "revenue": {
            "label": "Revenue this month",
            "value": numbers["revenue_month"],
            "money": True,
            "sub": timezone.localdate().strftime("%B %Y"),
            "icon": "bi-cash-coin",
            "color": "success",
            "url": "billing:payment_list",
        },
        "outstanding": {
            "label": "Outstanding balance",
            "value": numbers["outstanding"],
            "money": True,
            "sub": f"{numbers['open_invoices']} unpaid or partly paid invoices",
            "icon": "bi-receipt",
            "color": "danger",
            "url": "billing:invoice_list",
        },
        "low_stock": {
            "label": "Medicines at reorder level",
            "value": numbers["low_stock"],
            "sub": "at or below reorder level",
            "icon": "bi-capsule",
            "color": "warning",
            "url": "pharmacy:medicine_list",
        },
        "doctors": {
            "label": "Active doctors",
            "value": numbers["active_doctors"],
            "sub": f"{numbers['available_doctors']} taking appointments",
            "icon": "bi-person-badge-fill",
            "color": "secondary",
            "url": "staff:doctor_list",
        },
    }
    kpi_cards = [cards[key] for key in KPI_ORDER.get(user.role, DEFAULT_KPIS)]

    charts = {
        "intake": queries.patient_intake(scope),
        "status": queries.appointment_status(scope),
        "revenue": queries.revenue_by_month(scope),
        "medicines": queries.top_medicines(scope),
        "age_gender": queries.patients_by_age_gender(scope),
    }
    if not is_doctor:  # a doctor's own numbers make these one-bar charts
        charts["departments"] = queries.appointments_by_department(scope)
        charts["workload"] = queries.doctor_workload(scope)

    context = {
        "kpi_cards": kpi_cards,
        "charts": charts,
        "sections": SECTION_ORDER.get(user.role, DEFAULT_SECTIONS),
        "todays_appointments": queries.todays_appointments(scope),
        "low_stock": queries.low_stock_medicines(),
        "unpaid_invoices": queries.largest_unpaid_invoices(scope),
        "is_doctor": is_doctor,
    }
    return render(request, "analytics/dashboard.html", context)


REPORT_ROLES = (Role.ADMIN, Role.ACCOUNTANT, Role.RECEPTIONIST, Role.DOCTOR)


def _report_queryset(request, form):
    appointments = queries.scope_for(request.user).appointments
    if form.is_valid():
        appointments = queries.filter_appointments(appointments, form.cleaned_data)
    return appointments


@role_required(*REPORT_ROLES)
def reports(request):
    """Filter by date range, department, doctor and status; summary per doctor."""
    form = ReportFilterForm.from_request(request)
    appointments = _report_queryset(request, form)
    summary, totals = queries.doctor_summary(appointments)
    return render(
        request,
        "analytics/reports.html",
        {"form": form, "summary": summary, "totals": totals, "querystring": request.GET.urlencode()},
    )


@role_required(*REPORT_ROLES)
def export_csv(request):
    """Download the filtered report as CSV: one row per appointment."""
    form = ReportFilterForm.from_request(request)
    billed = (
        InvoiceItem.objects.filter(invoice__appointment=OuterRef("pk"))
        .values("invoice__appointment")
        .annotate(s=Sum(ExpressionWrapper(F("quantity") * F("unit_price"), output_field=MONEY)))
        .values("s")
    )
    paid = (
        Payment.objects.filter(invoice__appointment=OuterRef("pk"))
        .values("invoice__appointment")
        .annotate(s=Sum("amount"))
        .values("s")
    )
    zero = Value(0, output_field=MONEY)
    appointments = (
        _report_queryset(request, form)
        .select_related("patient", "doctor__user", "doctor__department", "medical_record", "invoice")
        .annotate(billed=Coalesce(Subquery(billed, output_field=MONEY), zero))
        .annotate(paid=Coalesce(Subquery(paid, output_field=MONEY), zero))
        .order_by("appointment_date", "appointment_time")
    )

    filename = f"hms-report-{timezone.localdate():%Y%m%d}.csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")  # BOM so Excel opens UTF-8 names correctly
    writer = csv.writer(response)
    writer.writerow(
        [
            "Date", "Time", "Patient code", "Patient", "Gender", "Age", "District", "Insurance",
            "Doctor", "Department", "Status", "Diagnosis", "Invoice", "Billed (RWF)", "Paid (RWF)", "Balance (RWF)",
        ]
    )
    for appt in appointments.iterator(chunk_size=500):
        patient = appt.patient
        record = getattr(appt, "medical_record", None)
        invoice = getattr(appt, "invoice", None)
        writer.writerow(
            [
                appt.appointment_date.isoformat(),
                appt.appointment_time.strftime("%H:%M"),
                patient.patient_code,
                patient.full_name,
                patient.get_gender_display(),
                patient.age,
                patient.district,
                patient.get_insurance_provider_display(),
                str(appt.doctor),
                appt.doctor.department.name,
                appt.get_status_display(),
                record.diagnosis if record else "",
                invoice.invoice_number if invoice else "",
                f"{appt.billed:.0f}",
                f"{appt.paid:.0f}",
                f"{appt.billed - appt.paid:.0f}",
            ]
        )
    return response
