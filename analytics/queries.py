"""ORM queries behind the dashboard and the reports page.

Every function takes a `Scope`, so a doctor's dashboard runs the same queries
narrowed to their own appointments ("doctors see only their own numbers").
Results are plain lists/dicts of str/float/int, ready for json_script.
"""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Case, CharField, Count, DecimalField, ExpressionWrapper, F, Q, QuerySet, Sum, Value, When
from django.db.models.functions import TruncMonth
from django.utils import timezone

from accounts.models import Role
from appointments.models import Appointment
from billing.models import Invoice, InvoiceItem, Payment
from patients.models import Patient
from pharmacy.models import Medicine, PrescriptionItem
from staff.models import Doctor

MONEY = DecimalField(max_digits=14, decimal_places=2)
AGE_BANDS = ["0-4", "5-14", "15-24", "25-44", "45-64", "65+"]


@dataclass
class Scope:
    appointments: QuerySet
    patients: QuerySet
    payments: QuerySet
    invoices: QuerySet
    prescription_items: QuerySet
    doctor: Doctor | None = None


def scope_for(user) -> Scope:
    if user.role == Role.DOCTOR:
        doctor = Doctor.objects.filter(user=user).first()
        return Scope(
            appointments=Appointment.objects.filter(doctor=doctor),
            patients=Patient.objects.filter(appointments__doctor=doctor).distinct(),
            payments=Payment.objects.filter(invoice__appointment__doctor=doctor),
            invoices=Invoice.objects.filter(appointment__doctor=doctor),
            prescription_items=PrescriptionItem.objects.filter(prescription__medical_record__appointment__doctor=doctor),
            doctor=doctor,
        )
    return Scope(
        appointments=Appointment.objects.all(),
        patients=Patient.objects.all(),
        payments=Payment.objects.all(),
        invoices=Invoice.objects.all(),
        prescription_items=PrescriptionItem.objects.all(),
    )


# --- helpers ---------------------------------------------------------------------------


def last_12_months(today: datetime.date | None = None) -> list[datetime.date]:
    """First day of each of the last 12 months, oldest first, ending this month."""
    today = today or timezone.localdate()
    year, month = today.year, today.month
    months = []
    for _ in range(12):
        months.append(datetime.date(year, month, 1))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(months))


def _month_key(value) -> tuple[int, int]:
    if isinstance(value, datetime.datetime):
        value = timezone.localtime(value) if timezone.is_aware(value) else value
    return value.year, value.month


def _series_by_month(rows, months, value_key="n"):
    found = {_month_key(row["month"]): row[value_key] for row in rows if row["month"]}
    return [float(found.get((m.year, m.month), 0) or 0) for m in months]


def _month_labels(months):
    """'Nov 2025' ... and 'Oct 2026 (to date)' for the month still in progress."""
    labels = [m.strftime("%b %Y") for m in months]
    labels[-1] += " (to date)"
    return labels


def _to_float(value) -> float:
    return float(value or 0)


# --- KPI cards -------------------------------------------------------------------------


def kpis(scope: Scope) -> dict:
    today = timezone.localdate()
    month_start = today.replace(day=1)

    todays = scope.appointments.filter(appointment_date=today).aggregate(
        total=Count("id"),
        scheduled=Count("id", filter=Q(status=Appointment.Status.SCHEDULED)),
        completed=Count("id", filter=Q(status=Appointment.Status.COMPLETED)),
    )
    return {
        "total_patients": scope.patients.count(),
        "new_patients_month": scope.patients.filter(created_at__date__gte=month_start).count(),
        "today_total": todays["total"],
        "today_scheduled": todays["scheduled"],
        "today_completed": todays["completed"],
        "revenue_month": _to_float(
            scope.payments.filter(paid_at__date__gte=month_start).aggregate(s=Sum("amount"))["s"]
        ),
        "outstanding": outstanding_balance(scope),
        "open_invoices": scope.invoices.open().count(),
        "low_stock": Medicine.objects.filter(stock_quantity__lte=F("reorder_level")).count(),
        "active_doctors": Doctor.objects.active().count(),
        "available_doctors": Doctor.objects.bookable().count(),
    }


def outstanding_balance(scope: Scope) -> float:
    """Sum of (invoice total - payments) over invoices that are not fully paid."""
    open_invoices = scope.invoices.open()
    billed = InvoiceItem.objects.filter(invoice__in=open_invoices).aggregate(
        s=Sum(ExpressionWrapper(F("quantity") * F("unit_price"), output_field=MONEY))
    )["s"] or Decimal("0")
    paid = Payment.objects.filter(invoice__in=open_invoices).aggregate(s=Sum("amount"))["s"] or Decimal("0")
    return _to_float(billed - paid)


# --- Charts ------------------------------------------------------------------------------


def patient_intake(scope: Scope) -> dict:
    """Line: new patients per month (12 months). Is patient intake growing?"""
    months = last_12_months()
    rows = (
        scope.patients.filter(created_at__date__gte=months[0])
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(n=Count("id", distinct=True))
        .order_by("month")
    )
    return {"labels": _month_labels(months), "values": _series_by_month(rows, months)}


def appointments_by_department(scope: Scope) -> dict:
    """Bar: which departments are busiest (last 12 months)?"""
    since = last_12_months()[0]
    rows = (
        scope.appointments.filter(appointment_date__gte=since)
        .values("doctor__department__name")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    return {
        "labels": [row["doctor__department__name"] for row in rows],
        "values": [row["n"] for row in rows],
    }


STATUS_ORDER = [
    Appointment.Status.COMPLETED,
    Appointment.Status.SCHEDULED,
    Appointment.Status.CANCELLED,
    Appointment.Status.NO_SHOW,
]


def appointment_status(scope: Scope) -> dict:
    """Doughnut: how many no-shows and cancellations (last 12 months)?"""
    since = last_12_months()[0]
    counts = dict(
        scope.appointments.filter(appointment_date__gte=since)
        .values("status")
        .annotate(n=Count("id"))
        .values_list("status", "n")
    )
    return {
        "labels": [status.label for status in STATUS_ORDER],
        "values": [counts.get(status.value, 0) for status in STATUS_ORDER],
    }


def revenue_by_month(scope: Scope) -> dict:
    """Bar: is income rising or falling? (sum of payments per month)"""
    months = last_12_months()
    rows = (
        scope.payments.filter(paid_at__date__gte=months[0])
        .annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    return {"labels": _month_labels(months), "values": _series_by_month(rows, months, "total")}


def top_medicines(scope: Scope, limit: int = 5) -> dict:
    """Horizontal bar: what drives pharmacy demand (units prescribed, 12 months)?"""
    since = last_12_months()[0]
    rows = (
        scope.prescription_items.filter(prescription__issued_at__date__gte=since)
        .values("medicine__name")
        .annotate(total=Sum("quantity"))
        .order_by("-total")[:limit]
    )
    return {"labels": [row["medicine__name"] for row in rows], "values": [row["total"] for row in rows]}


def _age_band_case(today: datetime.date):
    """CASE WHEN on date_of_birth: born after (today - N years) means younger than N."""

    def years_ago(n):
        try:
            return today.replace(year=today.year - n)
        except ValueError:  # 29 February
            return today.replace(year=today.year - n, day=28)

    return Case(
        When(date_of_birth__gt=years_ago(5), then=Value("0-4")),
        When(date_of_birth__gt=years_ago(15), then=Value("5-14")),
        When(date_of_birth__gt=years_ago(25), then=Value("15-24")),
        When(date_of_birth__gt=years_ago(45), then=Value("25-44")),
        When(date_of_birth__gt=years_ago(65), then=Value("45-64")),
        default=Value("65+"),
        output_field=CharField(),
    )


def patients_by_age_gender(scope: Scope) -> dict:
    """Grouped bar: who are our patients? Age bands split by gender."""
    patients = Patient.objects.filter(pk__in=scope.patients.values("pk"))
    rows = (
        patients.annotate(band=_age_band_case(timezone.localdate()))
        .values("band", "gender")
        .annotate(n=Count("id"))
    )
    counts = {(row["band"], row["gender"]): row["n"] for row in rows}
    return {
        "labels": AGE_BANDS,
        "male": [counts.get((band, Patient.Gender.MALE), 0) for band in AGE_BANDS],
        "female": [counts.get((band, Patient.Gender.FEMALE), 0) for band in AGE_BANDS],
    }


def doctor_workload(scope: Scope, limit: int = 10) -> dict:
    """Bar: who sees the most patients? Completed appointments, last 12 months."""
    since = last_12_months()[0]
    doctors = (
        Doctor.objects.active()
        .annotate(
            n=Count(
                "appointments",
                filter=Q(
                    appointments__status=Appointment.Status.COMPLETED,
                    appointments__appointment_date__gte=since,
                ),
            )
        )
        .select_related("user")
        .order_by("-n")[:limit]
    )
    return {"labels": [str(doctor) for doctor in doctors], "values": [doctor.n for doctor in doctors]}


# --- Alert tables ------------------------------------------------------------------------


def todays_appointments(scope: Scope):
    return (
        scope.appointments.filter(appointment_date=timezone.localdate())
        .select_related("patient", "doctor__user")
        .order_by("appointment_time")
    )


def low_stock_medicines(limit: int = 8):
    return Medicine.objects.filter(stock_quantity__lte=F("reorder_level")).order_by("stock_quantity")[:limit]


def largest_unpaid_invoices(scope: Scope, limit: int = 5):
    return (
        scope.invoices.open().with_totals().select_related("patient").order_by("-balance_amount")[:limit]
    )


# --- Reports page --------------------------------------------------------------------------


def filter_appointments(queryset: QuerySet, data: dict) -> QuerySet:
    """Apply the report filter form's cleaned_data to an Appointment queryset."""
    if data.get("date_from"):
        queryset = queryset.filter(appointment_date__gte=data["date_from"])
    if data.get("date_to"):
        queryset = queryset.filter(appointment_date__lte=data["date_to"])
    if data.get("department"):
        queryset = queryset.filter(doctor__department=data["department"])
    if data.get("doctor"):
        queryset = queryset.filter(doctor=data["doctor"])
    if data.get("status"):
        queryset = queryset.filter(status=data["status"])
    return queryset


def doctor_summary(appointments: QuerySet) -> tuple[list[dict], dict]:
    """One row per doctor plus a totals row: visits by status, billed and collected.

    Billed and collected are aggregated separately and merged in Python, because
    joining invoice items and payments in one query would double count.
    """
    rows = {
        row["doctor"]: row
        for row in appointments.values(
            "doctor", "doctor__user__first_name", "doctor__user__last_name", "doctor__department__name"
        )
        .annotate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=Appointment.Status.COMPLETED)),
            scheduled=Count("id", filter=Q(status=Appointment.Status.SCHEDULED)),
            cancelled=Count("id", filter=Q(status=Appointment.Status.CANCELLED)),
            no_show=Count("id", filter=Q(status=Appointment.Status.NO_SHOW)),
        )
        .order_by("doctor__department__name", "doctor__user__first_name")
    }
    billed = dict(
        InvoiceItem.objects.filter(invoice__appointment__in=appointments)
        .values("invoice__appointment__doctor")
        .annotate(s=Sum(ExpressionWrapper(F("quantity") * F("unit_price"), output_field=MONEY)))
        .values_list("invoice__appointment__doctor", "s")
    )
    collected = dict(
        Payment.objects.filter(invoice__appointment__in=appointments)
        .values("invoice__appointment__doctor")
        .annotate(s=Sum("amount"))
        .values_list("invoice__appointment__doctor", "s")
    )

    summary = []
    totals = {key: 0 for key in ["total", "completed", "scheduled", "cancelled", "no_show"]}
    totals.update(billed=Decimal("0"), collected=Decimal("0"))
    for doctor_id, row in rows.items():
        item = {
            "doctor": f"Dr. {row['doctor__user__first_name']} {row['doctor__user__last_name']}",
            "department": row["doctor__department__name"],
            "total": row["total"],
            "completed": row["completed"],
            "scheduled": row["scheduled"],
            "cancelled": row["cancelled"],
            "no_show": row["no_show"],
            "billed": billed.get(doctor_id) or Decimal("0"),
            "collected": collected.get(doctor_id) or Decimal("0"),
        }
        item["completion_rate"] = round(100 * item["completed"] / item["total"], 1) if item["total"] else 0
        summary.append(item)
        for key in totals:
            totals[key] += item[key]
    totals["completion_rate"] = round(100 * totals["completed"] / totals["total"], 1) if totals["total"] else 0
    totals["no_show_rate"] = round(100 * totals["no_show"] / totals["total"], 1) if totals["total"] else 0
    totals["collection_rate"] = (
        round(100 * float(totals["collected"]) / float(totals["billed"]), 1) if totals["billed"] else 0
    )
    return summary, totals
