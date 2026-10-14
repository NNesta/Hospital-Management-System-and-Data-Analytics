from django.conf import settings


def hospital(request):
    """Expose the hospital identity (name, address, TIN...) to every template."""
    return {"HOSPITAL": settings.HOSPITAL}
