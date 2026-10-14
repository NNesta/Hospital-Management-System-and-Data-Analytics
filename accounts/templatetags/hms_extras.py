"""Template filters shared by every app: money in RWF and status badges."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

register = template.Library()

STATUS_COLORS = {
    # appointments
    "SCHEDULED": "primary",
    "COMPLETED": "success",
    "CANCELLED": "secondary",
    "NO_SHOW": "warning",
    # pharmacy
    "PENDING": "warning",
    "DISPENSED": "success",
    # billing
    "UNPAID": "danger",
    "PARTIALLY_PAID": "warning",
    "PAID": "success",
}


@register.filter
def rwf(value):
    """Format a number as Rwandan francs: 15000 -> 'RWF 15,000'."""
    try:
        amount = Decimal(value or 0).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return value
    return f"RWF {amount:,.0f}"


@register.filter
def rwf_compact(value):
    """Short money for KPI tiles: 12_400_000 -> 'RWF 12.4M', 845000 -> 'RWF 845K'."""
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        return value
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(amount) >= threshold:
            short = f"{amount / threshold:.1f}".rstrip("0").rstrip(".")
            return f"RWF {short}{suffix}"
    return f"RWF {amount:,.0f}"


@register.filter
def status_color(status):
    return STATUS_COLORS.get(str(status), "secondary")


@register.inclusion_tag("partials/_status_badge.html")
def status_badge(obj):
    """Render <span class="badge">Label</span> for any model with a `status` field."""
    return {"label": obj.get_status_display(), "color": STATUS_COLORS.get(obj.status, "secondary")}


@register.filter
def has_role(user, roles):
    """{% if user|has_role:"ADMIN,RECEPTIONIST" %} - cosmetic only; views enforce access."""
    return getattr(user, "is_authenticated", False) and user.role in roles.split(",")


@register.simple_tag
def elided_pages(page_obj):
    """Page numbers with '…' gaps for long lists: 1 2 … 9 10 11 … 30."""
    return page_obj.paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)
