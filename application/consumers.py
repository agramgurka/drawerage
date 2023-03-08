import asyncio as aio
import logging
from random import shuffle
from typing import Optional

from channels.db import database_sync_to_async as to_async
from channels.exceptions import ChannelFull
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .services.basics import (Timer, GameStage, GameRole, GameScreens,
                              RoundStage, TaskType, StageTime, MEDIA_UPLOAD_DELAY, GAME_UPDATE_DELAY)
from .services.utils import display_task_result
from .services.db_function import (
    get_current_round, get_drawing_task, get_game_stage, finish_game,
    next_stage, get_players, get_role, get_variants,
    get_results, register_channel, create_rounds, calculate_results, stage_completed,
    create_results, is_game_paused, switch_pause_state, get_players_answers,
    get_finished_players, populate_missing_variants, deregister_channel)

logger = logging.getLogger(__name__)


class Game(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.game_id = None
        self.game_role = None
        self.global_group = None
        self.update_task = None
        self.previous_update = {}
        self.game_task = None
        self.paused = False
        super().__init__(*args, **kwargs)

    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        logger.info(f'start connection game: {self.game_id}, user: {self.scope["user"]}')
        self.game_role = await to_async(get_role)(user=self.scope['user'], game_id=self.game_id)

        if self.game_role:
            await to_async(register_channel)(self.game_id, self.scope['user'], self.channel_name)
            self.global_group = f'{self.game_id}_global'
            await self.channel_layer.group_add(
                self.global_group, self.channel_name
            )
            self.paused = await to_async(is_game_paused)(self.game_id)
            await self.accept()
            logger.info(f'connection accepted, role: {self.game_role}')
        else:
            await self.close()
            logger.info('connection declined')
            
    async def channel_send(self, channel_name, data):
        try:
            if channel_name:
                return await self.channel_layer.send(channel_name, data)
        except ChannelFull:
            logger.exception('Channel is FULL')

    async def disconnect(self, code):
        logger.info('disconnection begins')

        if self.game_role == GameRole.host:
            await self.cancel_tasks()
            if await to_async(get_game_stage)(self.game_id) != GameStage.finished:
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'game.paused',
                        'text': 'Host is disconnected'
                    }
                )
        await self.channel_layer.group_discard(
            self.global_group, self.channel_name
        )
        await to_async(deregister_channel)(self.game_id, self.scope['user'])
        logger.info('disconnected')

    async def receive_json(self, content, **kwargs):
        command = content.get('command')
        logger.info(f'command {command} received')

        if command == 'connected':
            if self.paused:
                await self.game_paused({'text': 'Game is paused'})
            await self.broadcast_updates()
            game_stage = await to_async(get_game_stage)(self.game_id)
            if self.game_role == GameRole.host:
                await self.send_stage()
                if game_stage not in [GameStage.pregame, GameStage.finished]:
                    self.game_task = aio.create_task(self.process_game())
                    self.game_task.add_done_callback(display_task_result)
                if not self.paused:
                    await self.channel_layer.group_send(
                        self.global_group,
                        {
                            'type': 'game.resumed'
                        }
                    )
                else:
                    await self.channel_layer.group_send(
                        self.global_group,
                        {
                            'type': 'game.paused',
                            'text': 'Game is paused'
                        }
                    )

        if self.game_role == GameRole.host:
            if command == 'start':
                try:
                    await to_async(create_rounds)(self.game_id)
                    await to_async(create_results)(self.game_id)
                    await to_async(next_stage)(self.game_id)

                    self.game_task = aio.create_task(self.process_game())
                    self.game_task.add_done_callback(display_task_result)
                    logger.info('game is started')
                except ValueError as e:
                    await self.send_json(
                        {
                            'command': 'error',
                            'error_type': 'start_game',
                            'error_message': str(e),
                        }
                    )

            if command == 'pause':
                await to_async(switch_pause_state)(self.game_id, pause=True)
                self.paused = True
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'game.paused',
                        'text': 'Game is paused'
                    }
                )
                logger.info('game is paused')

            if command == 'resume':
                await to_async(switch_pause_state)(self.game_id, pause=False)
                self.paused = False

                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'game.resumed'
                    }
                )
                logger.info('game is resumed')

            if command == 'cancel':
                await to_async(finish_game)(self.game_id)
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'game.paused',
                        'text': 'Game is cancelled'
                    }
                )

                logger.info('game is cancelled')

    async def process_game(self):
        try:
            logger.info('start processing game')
            while (game_stage := await to_async(get_game_stage)(self.game_id)) != GameStage.finished:
                if game_stage == GameStage.preround:
                    logger.info('start preround')
                    await self.process_stage(GameStage.preround)
                if game_stage == GameStage.round:
                    logger.info('start round')
                    game_round = await to_async(get_current_round)(self.game_id)
                    if game_round.painting:
                        if game_round.stage == RoundStage.writing:
                            logger.info('start writing')
                            await self.process_stage(GameStage.round, RoundStage.writing)
                        if game_round.stage == RoundStage.selecting:
                            await to_async(populate_missing_variants)(game_round)
                            logger.info('start selecting')
                            await self.process_stage(GameStage.round, RoundStage.selecting)
                        if game_round.stage == RoundStage.answers:
                            logger.info('show answers')
                            await aio.sleep(1)
                            await self.manage_answers_display(game_round)
                            await to_async(calculate_results)(self.game_id)
                        if game_round.stage == RoundStage.results:
                            logger.info('show result')
                            await self.process_stage(GameStage.round, RoundStage.results)
                logger.info('move to next stage')
                await to_async(next_stage)(self.game_id)
            await self.broadcast_updates()
        except aio.exceptions.CancelledError:
            pass

    async def process_stage(self, game_stage: GameStage, round_stage: Optional[RoundStage] = None):
        logger.info(f'start  {game_stage} stage')
        await self.broadcast_updates()

        if game_stage == GameStage.preround:
            stage_time = StageTime.preround
        elif round_stage == RoundStage.writing:
            stage_time = StageTime.writing
        elif round_stage == RoundStage.selecting:
            stage_time = StageTime.selecting
        elif round_stage == RoundStage.results:
            stage_time = StageTime.results
        else:
            raise ValueError('incorrect stage for processing')

        timer = Timer(int(stage_time / settings.GAME_SPEED))
        while not timer.exceed:
            if self.paused:
                await aio.sleep(1)
                continue
            if await to_async(stage_completed)(self.game_id, game_stage, round_stage):
                timer.time = -1
                logger.info('stage is completed before time exceeds')
            await self.broadcast_timer_update(stage_time, timer.time)
            await timer.tick()
        if game_stage == GameStage.preround or round_stage == RoundStage.writing:
            timer = Timer(MEDIA_UPLOAD_DELAY)
            while not await to_async(stage_completed)(self.game_id, game_stage, round_stage) and not timer.exceed:
                await timer.tick()
        logger.info('stage is over')

    async def broadcast_updates(self, event=None):
        logger.info('broadcasting updates')
        status_updates = {
            'active_screen': GameScreens.status,
            'players': {},
            'task_type': None
        }
        task_updates = {
            'active_screen': GameScreens.task,
            'task_type': None,
            'task': None
        }
        result_updates = {
            'active_screen': GameScreens.results,
        }
        answers_updates = {
            'active_screen': GameScreens.answers
        }

        players = await to_async(get_players)(self.game_id, host=True)
        game_stage = await to_async(get_game_stage)(self.game_id)

        for player in players:
            if not player.is_host:
                status_updates['players'][player.nickname] = {
                    'avatar': None if not player.avatar else player.avatar.url
                }

        if game_stage == GameStage.finished:
            results = await to_async(get_results)(self.game_id)
            result_updates['active_screen'] = GameScreens.final_standings
            result_updates['results'] = results
            await self.send_stage()
            await self.channel_layer.group_send(
                self.global_group,
                {
                    'type': 'send.update',
                    **result_updates,
                }
            )
        if game_stage == GameStage.pregame:
            status_updates['task_type'] = TaskType.drawing
            task_updates['task_type'] = TaskType.drawing
            task_updates['task'] = 'draw yourself'
            for player in players:
                if not player.is_host:
                    status_updates['players'][player.nickname]['finished'] = bool(player.avatar)
            for player in players:
                if player.avatar or player.is_host:
                    await self.channel_send(
                        player.channel_name,
                        {
                            'type': 'send.update',
                            **status_updates
                        }
                    )
                elif player.channel_name:
                    await self.channel_send(
                        player.channel_name,
                        {
                            'type': 'send.update',
                            **task_updates
                        }
                    )
        elif game_stage == GameStage.preround:
            status_updates['task_type'] = TaskType.drawing
            task_updates['task_type'] = TaskType.drawing
            drawing_tasks = {}
            for player in players:
                if not player.is_host:
                    drawing_tasks[player.pk] = await to_async(get_drawing_task)(self.game_id, player)
            finished_players = await to_async(get_finished_players)(self.game_id, game_stage)
            for player in players:
                if not player.is_host:
                    status_updates['players'][player.nickname]['finished'] = \
                        player.pk in finished_players
            for player in players:
                if player.is_host or status_updates['players'][player.nickname]['finished']:
                    await self.channel_send(
                        player.channel_name,
                        {
                            'type': 'send.update',
                            **status_updates
                        }
                    )
                else:
                    task_updates['task'] = drawing_tasks[player.pk]
                    await self.channel_send(
                        player.channel_name,
                        {
                            'type': 'send.update',
                            **task_updates
                        }
                    )
        elif game_stage == GameStage.round:
            try:
                game_round = await to_async(get_current_round)(self.game_id)
            except ObjectDoesNotExist:
                raise
            if game_round.stage == RoundStage.writing:
                status_updates['task_type'] = TaskType.writing
                task_updates['task_type'] = TaskType.writing
                task_updates['task'] = game_round.painting.url if game_round.painting else None
                finished_players = await to_async(get_finished_players)(self.game_id, game_stage,
                                                                        game_round)
                for player in players:
                    if not player.is_host:
                        status_updates['players'][player.nickname]['finished'] = \
                            player.pk in finished_players
                for player in players:
                    if player.is_host or status_updates['players'][player.nickname]['finished']:
                        await self.channel_send(
                            player.channel_name,
                            {
                                'type': 'send.update',
                                **status_updates
                            }
                        )
                    else:
                        await self.channel_send(
                            player.channel_name,
                            {
                                'type': 'send.update',
                                **task_updates
                            }
                        )
            elif game_round.stage == RoundStage.selecting:
                status_updates['task_type'] = TaskType.selecting
                task_updates['task_type'] = TaskType.selecting
                finished_players = await to_async(get_finished_players)(self.game_id, game_stage,
                                                                        game_round)
                variants = {}
                all_variants = await to_async(get_variants)(game_round)
                for player in players:
                    player_variants = [
                        variant for variant, user_id in all_variants
                        if user_id != player.pk
                    ]
                    shuffle(player_variants)
                    variants[player.pk] = player_variants
                for player in players:
                    if not player.is_host:
                        status_updates['players'][player.nickname]['finished'] = \
                            player.pk in finished_players
                for player in players:
                    if player.is_host or status_updates['players'][player.nickname]['finished']:
                        await self.channel_send(
                            player.channel_name,
                            {
                                'type': 'send.update',
                                **status_updates
                            }
                        )
                    else:
                        task_updates['task'] = {
                            'painting': game_round.painting.url if game_round.painting else None,
                            'variants': variants[player.pk],
                        }
                        await self.channel_send(
                            player.channel_name,
                            {
                                'type': 'send.update',
                                **task_updates
                            }
                        )
            elif game_round.stage == RoundStage.answers:
                answers = await to_async(get_variants)(game_round)
                answers = [variant for variant, _ in answers]
                shuffle(answers)
                answers_updates['variants'] = answers
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'send.update',
                        **answers_updates
                    }
                )
            elif game_round.stage == RoundStage.results:
                results = await to_async(get_results)(self.game_id)
                result_updates['results'] = results
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'send.update',
                        **result_updates
                    }
                )

    async def send_update(self, event: dict):
        if event != self.previous_update:
            await self.send_json(
                {
                    'command': 'update',
                    **event
                }
            )
            self.previous_update = event

    async def broadcast_timer_update(self, initial_time: int, time_left: int):
        await self.channel_layer.group_send(
            self.global_group,
            {
                'type': 'send.timer',
                'command': 'timer',
                'initial': initial_time,
                'left': time_left
            }
        )

    async def send_timer(self, event: dict):
        await self.send_json(event)

    async def send_stage(self):
        msg = {
            'command': 'init_stage',
            'stage': await to_async(get_game_stage)(self.game_id),
            }
        await self.send_json(msg)

    async def game_paused(self, event: dict):
        await self.send_json({
            'command': 'pause',
            **event
        }
        )

    async def game_resumed(self, event: dict):
        await self.send_json(
            {
                'command': 'resume',
            }
        )

    async def cancel_tasks(self):
        if self.update_task:
            self.update_task.cancel()
        if self.game_task:
            self.game_task.cancel()

    async def manage_answers_display(self, game_round):
        await self.broadcast_updates()
        answers = await to_async(get_players_answers)(game_round)
        is_correct = False
        while answers:
            if self.paused:
                await aio.sleep(1)
                continue
            if answers['incorrect']:
                variant = answers['incorrect'].pop()
            else:
                answers.pop('incorrect')
                variant = answers.pop('correct')
                is_correct = True
            await self.channel_layer.group_send(
                self.global_group,
                {
                    'type': 'display.answer',
                    'variant': variant,
                    'is_correct': is_correct
                }
            )
            time_for_selects = len(variant['selected_by']) or 1
            await aio.sleep(StageTime.for_one_answer.value + time_for_selects)

    async def display_answer(self, event):
        await self.send_json({
            'command': 'display_answer',
            'variant': event['variant'],
            'is_correct': event['is_correct']
        })
