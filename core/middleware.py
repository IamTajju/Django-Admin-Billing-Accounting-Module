from django.contrib.auth import authenticate, login
from django.conf import settings
from django.shortcuts import redirect


class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            user = authenticate(
                request, username=settings.DEMO_USERNAME, password=settings.DEMO_PASSWORD)
            if user is not None:
                login(request, user)
                return redirect(request.path)
        response = self.get_response(request)
        return response
