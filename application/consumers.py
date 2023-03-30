import asyncio as aio
import logging
from random import shuffle
from typing import Optional

from channels.db import database_sync_to_async as to_async
from channels.exceptions import ChannelFull
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .services.basics import (DISPLAY_SELECTED_DURATION, MEDIA_UPLOAD_DELAY,
                              WAIT_BEFORE_NEXT_ANSWER, GameRole, GameScreens,
                              GameStage, RoundStage, StageTime, TaskType,
                              Timer)
from .services.db_function import (calculate_likes, calculate_results,
                                   create_results, create_rounds,
                                   deregister_channel, finish_game,
                                   get_current_round, get_drawing_task,
                                   get_finished_players, get_game_stage,
                                   get_host_channel, get_players,
                                   get_players_answers, get_results, get_role,
                                   get_variants, is_game_paused, next_stage,
                                   populate_missing_variants, register_channel,
                                   stage_completed, switch_pause_state, get_active_game,
                                   create_game_from_existed, get_player_color)
from .services.utils import display_task_result

logger = logging.getLogger(__name__)


class Game(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.game_id = None
        self.game_role = None
        self.global_group = None
        self.previous_update = {}
        self.game_task = None
        self.paused = False
        self.variants = {}
        super().__init__(*args, **kwargs)

    async def connect(self):
        self.game_id = await to_async(get_active_game)(self.scope['user'])
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
            await self.channel_send(
                await to_async(get_host_channel)(self.game_id),
                {
                    'type': 'broadcast.updates'
                }
            )
            game_stage = await to_async(get_game_stage)(self.game_id)
            if self.game_role == GameRole.host:
                await self.init_buttons(game_stage)
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
                    logger.exception('Error with starting game command')
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
                        'type': 'game.cancelled',
                        'text': 'Game is cancelled',
                    }
                )

                logger.info('game is cancelled')
            if command == 'restart':
                logger.info('start new game with the same party')
                new_game_id = await to_async(create_game_from_existed)(self.game_id)
                logger.info(f'game {new_game_id} created')
                await self.channel_layer.group_send(
                    self.global_group,
                    {
                        'type': 'update.meta',
                        'new_game_id': new_game_id
                    }
                )
                await self.channel_send(
                    self.channel_name,
                    {
                        'type': 'broadcast.updates'
                    }
                )
                await self.init_buttons(GameStage.pregame)

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
                            self.variants = {}
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
            'task_type': None,
            'task': None
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

        players = await to_async(get_players)(self.game_id)
        game_stage = await to_async(get_game_stage)(self.game_id)

        for player in players:
            status_updates['players'][player.pk] = {
                'avatar': None if not player.avatar else player.avatar.url,
                'nickname': player.nickname
            }

        if game_stage == GameStage.finished:
            result_updates['active_screen'] = GameScreens.final_standings
            final_results = []
            for result in await to_async(get_results)(self.game_id):
                result['likes_cnt'] = await to_async(calculate_likes)(result['player__pk'])
                result.pop('player__pk')
                result.pop('round_increment')
                final_results.append(result)
            result_updates['results'] = final_results
            await self.init_buttons(GameStage.finished)
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
                status_updates['players'][player.pk]['finished'] = bool(player.avatar)
            for player in players:
                if player.avatar:
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
                drawing_tasks[player.pk] = await to_async(get_drawing_task)(self.game_id, player)
            finished_players = await to_async(get_finished_players)(self.game_id, game_stage)
            for player in players:
                status_updates['players'][player.pk]['finished'] = \
                    player.pk in finished_players
            for player in players:
                if status_updates['players'][player.pk]['finished']:
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
                status_updates['task'] = game_round.painting.url if game_round.painting else None
                task_updates['task_type'] = TaskType.writing
                task_updates['task'] = game_round.painting.url if game_round.painting else None
                finished_players = await to_async(get_finished_players)(self.game_id, game_stage,
                                                                        game_round)
                for player in players:
                    status_updates['players'][player.pk]['finished'] = \
                        player.pk in finished_players
                for player in players:
                    if status_updates['players'][player.pk]['finished']:
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
                if not self.variants:
                    self.variants['all_variants'] = await to_async(get_variants)(game_round)
                    shuffle(self.variants['all_variants'])
                    for player in players:
                        player_variants = [
                            variant for _, variant, user_id in self.variants['all_variants']
                            if user_id != player.pk
                        ]
                        shuffle(player_variants)
                        self.variants[player.pk] = player_variants
                status_updates['task'] = [variant for _, variant, _ in self.variants['all_variants']]
                for player in players:
                    status_updates['players'][player.pk]['finished'] = \
                        player.pk in finished_players
                for player in players:
                    if status_updates['players'][player.pk]['finished']:
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
                            'variants': self.variants[player.pk],
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
                shuffle(answers)
                for player in players:
                    player_answers = [
                        {
                            'id': pk,
                            'text': variant,
                            'likable': player.pk != author_id
                        }
                        for pk, variant, author_id in answers
                    ]
                    answers_updates['variants'] = player_answers
                    await self.channel_send(
                        player.channel_name,
                        {
                            'type': 'send.update',
                            **answers_updates
                        }
                    )
            elif game_round.stage == RoundStage.results:
                results = await to_async(get_results)(self.game_id)
                for result in results:
                    result.pop('player__pk')
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

    async def init_buttons(self, game_stage: GameStage):
        await self.send_json(
            {
                'command': 'init_buttons',
                'stage': game_stage,
            }
        )

    async def game_paused(self, event: dict):
        await self.send_json({
            'command': 'pause',
            'text': event['text']
        }
        )

    async def game_cancelled(self, event: dict):
        await self.send_json({
            'command': 'cancel',
            'text': event['text']
        }
        )

    async def game_resumed(self, event: dict):
        await self.send_json(
            {
                'command': 'resume',
            }
        )

    async def cancel_tasks(self):
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
            time_for_selects = (len(variant['selected_by']) or 1) * DISPLAY_SELECTED_DURATION
            await aio.sleep(StageTime.for_one_answer.value + time_for_selects + WAIT_BEFORE_NEXT_ANSWER)
        await self.channel_layer.group_send(
            self.global_group,
            {
                'type': 'collect.likes',
            }
        )

    async def collect_likes(self, event):
        await self.send_json({
            'command': 'collect_likes'
        })

    async def display_answer(self, event):
        await self.send_json({
            'command': 'display_answer',
            'variant': event['variant'],
            'is_correct': event['is_correct']
        })

    async def update_meta(self, event):
        self.game_id = event['new_game_id']
        await self.channel_layer.group_discard(
            self.global_group, self.channel_name
        )
        self.global_group = f'{self.game_id}_global'
        await self.channel_layer.group_add(
            self.global_group, self.channel_name
        )
        await to_async(register_channel)(self.game_id, self.scope['user'], self.channel_name)
        await self.send_json(
            {
                'command': 'update_colors',
                'main_color': await to_async(get_player_color)(event['new_game_id'], self.scope['user'])
            }
        )
        logger.debug('meta is updated')