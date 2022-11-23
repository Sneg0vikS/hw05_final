from django.utils import timezone


def year(request):
    """Добавлям переменную с текущим годом."""
    dt = timezone.now().year
    return {'year': dt}
