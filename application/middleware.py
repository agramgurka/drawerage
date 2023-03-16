from django.contrib.auth import login
from django.http import HttpRequest

from .services.db_function import create_user


class ImplicitLogInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if not request.user.is_authenticated:
            new_user = create_user()
            login(request, new_user)
        response = self.get_response(request)
        return response
