from django.urls import path
from .views import StartPage, CreateGame, Game, Proxy, MediaUpload

urlpatterns = [
    path('', Proxy.as_view(), name='proxy'),
    path('start/', StartPage.as_view(), name='start_page'),
    path('create/', CreateGame.as_view(), name='create_game'),
    path('game/<int:pk>', Game.as_view(), name='game'),
    path('upload/', MediaUpload.as_view(), name='media_upload')
]
