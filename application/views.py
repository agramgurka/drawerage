import json
import logging

from channels.db import database_sync_to_async as to_async
from channels.layers import get_channel_layer
from django.core.exceptions import (MultipleObjectsReturned,
                                    ObjectDoesNotExist, ValidationError)
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView

from .forms import CreateGameForm, JoinGameForm
from .services.basics import GameStage, MediaType
from .services.db_function import (apply_variant, create_game, get_active_game,
                                   get_game_code, get_game_stage,
                                   get_host_channel, get_player_color, is_host,
                                   is_player, join_game, select_variant,
                                   upload_avatar, upload_painting)

logger = logging.getLogger(__name__)


class StartPage(FormView):
    template_name = 'start_page.html'
    form_class = JoinGameForm
    game_id = None

    def get(self, request, *args, **kwargs):
        active_game = get_active_game(request.user)
        if active_game:
            return redirect(reverse('game'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['new_game_form'] = CreateGameForm()
        return ctx

    def form_valid(self, form):
        game_code = form.cleaned_data['game_code']
        nickname = form.cleaned_data['player_nickname']
        try:
            self.game_id = join_game(self.request, game_code=game_code, nickname=nickname)
            return super().form_valid(form)
        except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError):
            return super().form_invalid(form)

    def get_success_url(self):
        return reverse('game')


class CreateGame(FormView):
    form_class = CreateGameForm

    def form_valid(self, form):
        create_game(self.request, language_code=form.cleaned_data['language'])
        return redirect(reverse('game'))

    def form_invalid(self, form):
        return redirect(reverse('start_page'))

    def get_success_url(self):
        return reverse('game')


class Game(View):
    def get(self, request):
        game_id = get_active_game(request.user)
        if not is_player(game_id, request.user):
            return redirect('start_page')
        drawing_color = get_player_color(game_id, request.user)
        context = {'game_id': game_id, 'drawing_color': drawing_color}
        if is_host(game_id, request.user):
            context['game_code'] = get_game_code(game_id)
        return render(request, 'game.html', context)


class MediaUpload(View):
    """ all the paintings and variants are applied through this view """

    channel_layer = get_channel_layer()

    async def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        media_type = data.get('media_type')
        game_id = data.get('game_id')
        media = data.get('media')
        status = 'error'
        message = None
        status_code = 200
        if media_type == MediaType.painting_task:
            game_stage = await to_async(get_game_stage)(game_id)
            if game_stage == GameStage.pregame:
                try:
                    await to_async(upload_avatar)(game_id, request.user, media)
                    status = 'success'
                except ValidationError as e:
                    status = e.code
                    message = e.message
                    status_code = 400
            if game_stage == GameStage.preround:
                try:
                    await to_async(upload_painting)(game_id, request.user, media)
                    status = 'success'
                except ValidationError as e:
                    status = e.code
                    message = e.message
                    status_code = 400
        if media_type == MediaType.variant:
            try:
                await to_async(apply_variant)(game_id, request.user, media)
                status = 'success'
            except ValidationError as e:
                status = e.code
                message = e.message
                status_code = 400
        if media_type == MediaType.answer:
            try:
                await to_async(select_variant)(game_id, request.user, media)
                status = 'success'
            except ValidationError as e:
                status = e.code
                message = e.message
                status_code = 400
        if status_code == 200:
            host_channel = await to_async(get_host_channel)(game_id)
            logger.debug(host_channel)
            await self.channel_layer.send(
                host_channel,
                {
                    'type': 'broadcast.updates'
                }
            )
        return JsonResponse({'status': status, 'message': message}, status=status_code)
