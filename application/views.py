import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError

from .services.db_function import (join_game, create_game, get_active_game,
                                   upload_avatar, upload_painting,
                                   apply_variant, select_variant, get_game_stage,
                                   get_player_color)
from .services.basics import MediaType, GameStage
from .services.utils import setup_logger
from .forms import JoinGameForm

logger = setup_logger(__name__)


class StartPage(FormView):
    template_name = 'start_page.html'
    form_class = JoinGameForm
    game_id = None

    def get(self, request, *args, **kwargs):
        active_game = get_active_game(request.user)
        if active_game:
            return redirect(reverse('game', args=[active_game]))
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        game_code = form.cleaned_data['game_code']
        nickname = form.cleaned_data['player_nickname']
        try:
            self.game_id = join_game(self.request, game_code=game_code, nickname=nickname)
            return super().form_valid(form)
        except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError):
            return super().form_invalid(form)

    def get_success_url(self):
        return reverse('game', args=[self.game_id])


class CreateGame(View):
    def get(self, request):
        game_id = create_game(request)
        return redirect(reverse('game', args=[game_id]))


class Game(View):
    def get(self, request, pk):
        if get_game_stage(pk) == GameStage.finished:
            return redirect('start_page')
        drawing_color = get_player_color(pk, request.user)
        return render(request, 'game.html', {'game_id': pk, 'drawing_color': drawing_color})


class MediaUpload(View):
    """ all the paintings and variants are applied through this view """

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        media_type = data.get('media_type')
        game_id = data.get('game_id')
        media = data.get('media')
        status = 'error'
        status_code = 200
        if media_type == MediaType.painting_task:
            game_stage = get_game_stage(game_id)
            if game_stage == GameStage.pregame:
                try:
                    upload_avatar(game_id, request.user, media)
                    status = 'success'
                except ValidationError:
                    status = 'duplicate'
                    status_code = 400
            if game_stage == GameStage.preround:
                try:
                    upload_painting(game_id, request.user, media)
                    status = 'success'
                except ValidationError:
                    status = 'duplicate'
                    status_code = 400
        if media_type == MediaType.variant:
            try:
                apply_variant(game_id, request.user, media)
                status = 'success'
            except ValidationError:
                status = 'duplicate'
                status_code = 400
        if media_type == MediaType.answer:
            try:
                select_variant(game_id, request.user, media)
                status = 'success'
            except ValidationError:
                status = 'duplicate'
                status_code = 400
        return JsonResponse({'status': status}, status=status_code)

