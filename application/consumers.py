import asyncio as aio
from random import shuffle
from typing import Optional

from channels.db import database_sync_to_async as to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .services.basics import (Timer, GameStage, GameRole, GameScreens,
                              RoundStage, TaskType, StageTime, MEDIA_UPLOAD_DELAY)
from .services.utils import setup_logger, display_task_result
from .services.db_function import (
    get_current_round, get_drawing_task, get_game_stage, finish_game,
    next_stage, get_players, get_role, finished_painting,
    applied_variant, selected_variant, get_variants, get_game_code,
    get_results, register_channel, create_rounds, calculate_results, stage_completed,
    create_results, is_game_paused, switch_pause_state)


logger = setup_logger(__name__)


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

    async def disconnect(self, code):
        logger.info('disconnection begins')

        if self.game_role == GameRole.host:
            await self.cancel_tasks()
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
        logger.info('disconnected')

    async def receive_json(self, content, **kwargs):
        command = content.get('command')
        logger.info(f'command {command} received')

        if command == 'connected':
            await self.send_game_state()
            if self.game_role == GameRole.host:
                self.update_task = aio.create_task(self.broadcast_game_updates())
                self.update_task.add_done_callback(display_task_result)
                game_stage = await to_async(get_game_stage)(self.game_id)
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
        if self.game_role == GameRole.host:
            if command == 'start':
                await to_async(create_rounds)(self.game_id)
                await to_async(create_results)(self.game_id)
                await to_async(next_stage)(self.game_id)

                self.game_task = aio.create_task(self.process_game())
                self.game_task.add_done_callback(display_task_result)
                logger.info('game is started')

            if command == 'pause':
                await to_async(switch_pause_state)(self.game_id, pause=True)
                self.paused = True
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'game.paused',
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
                        'text': 'game is cancelled'
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
                            logger.info('start selecting')
                            await self.process_stage(GameStage.round, RoundStage.selecting)
                            await to_async(calculate_results)(self.game_id)
                        if game_round.stage == RoundStage.results:
                            logger.info('show result')
                            await self.process_stage(GameStage.round, RoundStage.results)
                logger.info('move to next stage')
                await to_async(next_stage)(self.game_id)
        except aio.exceptions.CancelledError:
            pass

    async def process_stage(self, game_stage: GameStage, round_stage: Optional[RoundStage] = None):
        logger.info(f'start  {game_stage} stage')

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

        timer = Timer(stage_time)
        while not timer.exceed:
            if not self.paused:
                await self.broadcast_timer_update(timer.time)
                await timer.tick()
                if await to_async(stage_completed)(self.game_id, game_stage, round_stage):
                    timer.time = -1
                    logger.info('stage is completed before time exceeds')
            else:
                await aio.sleep(1)
        if game_stage == GameStage.preround or round_stage == RoundStage.writing:
            timer = Timer(MEDIA_UPLOAD_DELAY)
            while not await to_async(stage_completed)(self.game_id, game_stage, round_stage) and not timer.exceed:
                await timer.tick()
        logger.info('stage is over')

    async def broadcast_game_updates(self):
        try:
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

            players = await to_async(get_players)(self.game_id)
            for player in players:
                avatar_url = None if not player.avatar else player.avatar.url
                status_updates['players'][player.nickname] = {
                    'avatar': avatar_url
                }

            current_round = None
            all_variants = None
            while True:
                if not self.paused:
                    players = await to_async(get_players)(self.game_id, host=True)
                    game_stage = await to_async(get_game_stage)(self.game_id)

                    if game_stage == GameStage.finished:
                        break
                    elif game_stage == GameStage.pregame:
                        for player in players:
                            if not player.is_host:
                                avatar_url = None if not player.avatar else player.avatar.url
                                status_updates['players'][player.nickname] = {
                                    'avatar': avatar_url,
                                    'finished': bool(player.avatar)
                                }

                        status_updates['task_type'] = TaskType.drawing
                        task_updates['task_type'] = TaskType.drawing
                        task_updates['task'] = 'draw yourself'
                        for player in players:
                            if player.avatar or player.is_host:
                                await self.channel_layer.send(
                                    player.channel_name,
                                    {
                                        'type': 'send.update',
                                        **status_updates
                                    }
                                )
                            elif player.channel_name:
                                await self.channel_layer.send(
                                    player.channel_name,
                                    {
                                        'type': 'send.update',
                                        **task_updates
                                    }
                                )

                    elif game_stage == GameStage.preround:
                        status_updates['task_type'] = TaskType.drawing
                        task_updates['task_type'] = TaskType.drawing
                        for player in players:
                            if not player.is_host:
                                status_updates['players'][player.nickname]['finished'] = \
                                    await to_async(finished_painting)(self.game_id, player)
                        for player in players:
                            if player.is_host or status_updates['players'][player.nickname]['finished']:
                                await self.channel_layer.send(
                                    player.channel_name,
                                    {
                                        'type': 'send.update',
                                        **status_updates
                                    }
                                )
                            else:
                                task_updates['task'] = await to_async(get_drawing_task)(self.game_id, player)
                                await self.channel_layer.send(
                                    player.channel_name,
                                    {
                                        'type': 'send.update',
                                        **task_updates
                                    }
                                )

                    elif game_stage == GameStage.round:
                        game_round = await to_async(get_current_round)(self.game_id)
                        if game_round.stage == RoundStage.writing:
                            status_updates['task_type'] = TaskType.writing
                            task_updates['task_type'] = TaskType.writing
                            if not game_round.painting:
                                continue
                            task_updates['task'] = game_round.painting.url
                            for player in players:
                                if not player.is_host:
                                    status_updates['players'][player.nickname]['finished'] = \
                                        await to_async(applied_variant)(game_round, player)
                            for player in players:
                                if player.is_host or status_updates['players'][player.nickname]['finished']:
                                    await self.channel_layer.send(
                                        player.channel_name,
                                        {
                                            'type': 'send.update',
                                            **status_updates
                                        }
                                    )
                                else:
                                    await self.channel_layer.send(
                                        player.channel_name,
                                        {
                                            'type': 'send.update',
                                            **task_updates
                                        }
                                    )

                        elif game_round.stage == RoundStage.selecting:
                            status_updates['task_type'] = TaskType.selecting
                            task_updates['task_type'] = TaskType.selecting

                            if all_variants is None or current_round != game_round:
                                current_round = game_round
                                variants = await to_async(get_variants)(game_round)

                                all_variants = {}
                                for player in players:
                                    player_variants = [
                                        variant for variant, user_id in variants
                                        if user_id != player.pk
                                    ]
                                    shuffle(player_variants)
                                    all_variants[player.pk] = player_variants

                            for player in players:
                                if not player.is_host:
                                    status_updates['players'][player.nickname]['finished'] = \
                                        await to_async(selected_variant)(game_round, player)
                            for player in players:
                                if player.is_host or status_updates['players'][player.nickname]['finished']:
                                    await self.channel_layer.send(
                                        player.channel_name,
                                        {
                                            'type': 'send.update',
                                            **status_updates
                                        }
                                    )
                                else:
                                    task_updates['task'] = all_variants[player.pk]
                                    await self.channel_layer.send(
                                        player.channel_name,
                                        {
                                            'type': 'send.update',
                                            **task_updates
                                        }
                                    )

                        elif game_round.stage == RoundStage.results:
                            result_updates['results'] = await to_async(get_results)(self.game_id)
                            for player in players:
                                await self.channel_layer.send(
                                    player.channel_name,
                                    {
                                            'type': 'send.update',
                                            **result_updates
                                        }
                                    )

                await aio.sleep(0.2)
            logger.info('updates broadcast is finished')
        except aio.exceptions.CancelledError:
            pass

    async def send_update(self, event: dict):
        if event != self.previous_update:
            await self.send_json(
                {
                    'command': 'update',
                    **event
                }
            )
            self.previous_update = event

    async def broadcast_timer_update(self, time: int):
        await self.channel_layer.group_send(
            self.global_group,
            {
                'type': 'send.timer',
                'command': 'timer',
                'time': time
            }
        )

    async def send_timer(self, event: dict):
        await self.send_json(event)

    async def send_game_state(self):
        state = {
            'command': 'state',
            'is_paused': self.paused,
        }
        if self.game_role == GameRole.host:
            state.update({
                'game_code': await to_async(get_game_code)(self.game_id),
                'stage': await to_async(get_game_stage)(self.game_id),
            })
        await self.send_json(state)

    async def game_paused(self, event: dict):
        await self.send_json({
            'command': 'pause',
            **event
        }
        )

    async def game_resumed(self, event: dict):
        await self.send_json({
            'command': 'resume',
        }
        )

    async def cancel_tasks(self):
        if self.update_task:
            self.update_task.cancel()
        if self.game_task:
            self.game_task.cancel()



