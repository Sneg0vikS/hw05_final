from django.shortcuts import render


def page_not_found(request, exception):
    """Страница не найденна 404 ошибка"""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    """Ошибка csrf токена 403csrf ошибка"""
    return render(request, 'core/403csrf.html')


def page_forbidden(request, exception):
    """Доступ к запрошенному ресурсу запрещён 403 ошибка"""
    return render(request, 'core/403.html', {'path': request.path}, status=403)


def page_internal_server_error(request, *args, **argv):
    """Сервер не может обработать запрос 500 ошибка"""
    return render(request, 'core/500.html', {'path': request.path}, status=500)
