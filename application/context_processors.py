from django.conf import settings


def site_settings(request):
    return {'game_title': settings.GAME_TITLE, 'game_slogan': settings.GAME_SLOGAN}