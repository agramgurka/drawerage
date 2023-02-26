from django.urls import path
from .views import StartPage, CreateGame, Game, MediaUpload

urlpatterns = [
    path('', StartPage.as_view(), name='start_page'),
    path('create/', CreateGame.as_view(), name='create_game'),
    path('game/', Game.as_view(), name='game'),
    path('upload/', MediaUpload.as_view(), name='media_upload')
]
