import base64
import logging
import random
import re
from functools import lru_cache
from typing import Optional

from more_itertools import distinct_combinations

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import F, Count, Q
from django.http import HttpRequest
from django.core.files.base import ContentFile
from thefuzz import fuzz

from ..models import Player, Game, Round, Variant, Result, Language
from .auto_answers import get_auto_answers
from .basics import (DRAWING_COLORS,
                     GameRole, GameStage, RoundStage,
                     POINTS_FOR_CORRECT_ANSWER,
                     POINTS_FOR_RECOGNITION,
                     POINTS_FOR_CORRECT_RECOGNITION,
                     GAME_CODE_LEN, USERNAME_LEN, CODE_CHARS,)
from .tasks import BaseTaskProducer, PredefinedTaskProducer, Restriction, RuslangTaskProducer

logger = logging.getLogger(__name__)


MIN_SIMILARITY_RANK = 92

# words should contain only cyrillic or only latin letters
VARIANT_VALIDATION_RX = re.compile(r'((([\s0-9\u0400-\u0454\u00cb]+)\b|([0-9a-zA-Z]+)\b)[-%&_–—.!?/\\\s]*)+$')


def generate_game_code(code_len=GAME_CODE_LEN) -> str:
    """ generates and returns unique shortcode for a game; """

    while True:
        code = ''.join(random.choices(CODE_CHARS, k=code_len))
        if not Game.objects.filter(code=code).exclude(stage=GameStage.finished).exists():
            return code


def generate_username(name_len=USERNAME_LEN):
    while True:
        new_username = ''.join(random.choices(population=CODE_CHARS, k=name_len))
        if not User.objects.filter(username=new_username).exists():
            return new_username


def create_user() -> User:
    """ creates new user object in database """

    user = User.objects.create_user(username=generate_username())
    return user


def register_channel(game_id: int, user: User, channel_name: str):
    """ registers player's websocket channel name"""

    Player.objects.filter(game_id=game_id, user=user).update(channel_name=channel_name)


def deregister_channel(game_id: int, user: User):
    """ deregisters player's websocket channel name"""

    Player.objects.filter(game_id=game_id, user=user).update(channel_name=None)


def create_player(game_id: int, user: User, nickname: str = None, is_host: bool = False) -> Player:
    """ creates player's record """

    color = None
    if not is_host:
        color = pick_color(game_id)

    return Player.objects.create(game_id=game_id, user=user, nickname=nickname, is_host=is_host, drawing_color=color)


def pick_color(game_id: int) -> str:
    all_colors = [x.lower() for x in DRAWING_COLORS]
    random.shuffle(all_colors)
    mixer_stage = 1
    while True:
        if not all_colors:
            mixer_stage += 1
            if mixer_stage > len(DRAWING_COLORS):
                raise ValueError('number of players is greater than number of drawing colors')

            all_colors = [
                '#' + hex(sum((int(x[1:], 16) for x in colors)) // mixer_stage)
                for colors in distinct_combinations(DRAWING_COLORS, mixer_stage)
            ]
            random.shuffle(all_colors)
        color = all_colors.pop()
        if not Player.objects.filter(game_id=game_id, drawing_color=color).exists():
            return color


def is_player(game_id: int, user: User) -> bool:
    return Game.objects.filter(pk=game_id, players__user=user).exists()


def create_game(request, *, language_code, cycles=2) -> int:
    """ creates new game object and adds game's host to it """
    language = Language.objects.get(code=language_code)
    game = Game.objects.create(code=generate_game_code(), cycles=cycles, language=language)
    host = create_player(game_id=game.pk, user=request.user, is_host=True)
    game.players.add(host)
    return game.pk


def get_player_color(game_id: int, user: User) -> str:
    """ returns player's drawing color """

    return user.player_set.get(game_id=game_id).drawing_color


def get_active_game(user: User) -> Optional[int]:
    """ returns id of player's/host's active game, if it exists"""

    if user.is_authenticated:
        active_game = Game.objects.filter(players__user=user).exclude(
            stage=GameStage.finished,
        ).only('pk').order_by('-pk').first()
        if active_game:
            return active_game.pk
    return None


def get_game_code(game_id: int) -> str:
    """ returns game code """

    return Game.objects.get(pk=game_id).code


def join_game(request: HttpRequest, game_code: str, nickname: str) -> Optional[int]:
    """ if game exists, adds user to players; returns game id"""

    game = Game.objects.get(code=game_code.upper())
    if game.stage == GameStage.pregame:
        if not request.user.player_set.filter(game=game).exists():
            player = create_player(game_id=game.pk, user=request.user, nickname=nickname)
            game.players.add(player)
        return game.pk
    else:
        raise ValueError('Game has already begun')


@lru_cache()
def get_predefined_task_producer(lang: Language) -> PredefinedTaskProducer | None:
    try:
        return PredefinedTaskProducer(lang)
    except ValueError:
        return None


@lru_cache()
def get_ruslang_task_producer(lang) -> RuslangTaskProducer | None:
    try:
        return RuslangTaskProducer(lang)
    except ValueError:
        return None


def available_task_producers(lang: Language) -> list[tuple[BaseTaskProducer, int]]:
    """
    Returns provider and weight how ofter it should appears
    """
    return [x for x in [
        # predefined tasks from database
        (get_predefined_task_producer(lang), 5),
        # random phrase from ruslang
        (get_ruslang_task_producer(lang), 2),
    ] if x[0] is not None]


def create_drawing_task(game: Game, restrictions) -> tuple[str, Restriction]:
    """ returns new painting task """

    producers_with_weights = available_task_producers(game.language)
    return random.choices(
        [x for x, _ in producers_with_weights],
        weights=[x for _, x in producers_with_weights],
    )[0].get_task(restrictions)


def create_rounds(game_id: int) -> None:
    """ creates rounds for game """

    players = get_players(game_id)
    if len(players) < 2:
        raise ValueError('At least two players are required to start the game')
    game = Game.objects.get(pk=game_id)
    restrictions = None
    for order_number, player in enumerate(players * game.cycles):
        task, restrictions = create_drawing_task(game, restrictions)
        game_round = Round.objects.create(
            game=game,
            order_number=order_number,
            painter=player,
            painting_task=task,
        )
        Variant.objects.create(
            text=task,
            author=player,
            game_round=game_round
        )


def create_results(game_id: int):
    game = Game.objects.get(pk=game_id)
    for player in get_players(game_id):
        Result.objects.create(
            game=game,
            player=player
                             )


def get_current_round(game_id: int) -> Round:
    """ returns current game round """

    return Round.objects.exclude(
        stage__in=[RoundStage.not_started, RoundStage.finished]
    ).get(
        game=game_id
    )


def get_players(game_id: int, host: bool = False) -> list:
    """ returns list of players """

    if host:
        return list(Player.objects.filter(game_id=game_id))
    return list(Player.objects.filter(game_id=game_id, is_host=False))


def get_game_stage(game_id: int) -> Optional[str]:
    """ returns current game stage """
    try:
        return Game.objects.get(pk=game_id).stage
    except ObjectDoesNotExist:
        return None


def get_role(user: User, game_id: int) -> Optional[GameRole]:
    """ returns player game role: player or host"""

    player = Player.objects.filter(game_id=game_id, user=user).first()
    if not player:
        return None
    return GameRole.host if player.is_host else GameRole.player


def get_finished_players(game_id: int, game_stage: GameStage, game_round: Round = None) -> list:
    finished_players = None
    if game_stage == GameStage.preround:
        finished_players = Round.objects.filter(
            game=game_id,
            stage=RoundStage.not_started
        ).exclude(
            painting__exact=''
        ).values_list('painter__pk', flat=True)
    else:
        if game_round.stage == RoundStage.writing:
            finished_players = Variant.objects.filter(game_round=game_round).values_list('author__pk', flat=True)
        if game_round.stage == RoundStage.selecting:
            finished_players = Variant.objects.filter(
                game_round=game_round
            ).exclude(selected_by=None).values_list('selected_by__pk', flat=True)

    finished_players = [*finished_players]
    if game_round and game_round.stage == RoundStage.selecting:
        finished_players.append(game_round.painter.pk)
    return finished_players


def get_drawing_task(game_id: int, player: Player) -> str:
    """ returns player's painting task for a cycle """

    return Round.objects.filter(
        game=game_id,
        painter=player,
        stage=RoundStage.not_started
    ).first().painting_task


def get_variants(game_round: Round) -> list[tuple[str, int | None]]:
    """ returns players' and auto generated variants for a round """

    return list(Variant.objects.filter(
        game_round=game_round,
    ).order_by('id').values_list('text', 'author_id'))


def get_results(game: Game):
    """ returns game's results """

    return list(Result.objects.filter(game=game).values(
        'player__nickname', 'player__avatar', 'player__drawing_color', 'result', 'round_increment'
    ))


def next_stage(game_id: int):
    """ switch game stage """

    logger.debug('next stage function')
    game = Game.objects.get(pk=game_id)
    logger.debug(f'game stage before: {game.stage}')
    if game.stage == GameStage.pregame:
        game.stage = GameStage.preround
        game.save()
    elif game.stage == GameStage.preround:
        game.stage = GameStage.round
        game.save()
        next_round = Round.objects.filter(
            game=game_id,
            stage=RoundStage.not_started
        ).first()
        next_round.stage = RoundStage.writing
        next_round.save()

    elif game.stage == GameStage.round:
        game_round = get_current_round(game_id)
        logger.debug(f'round stage before: {game_round.stage}')
        if game_round.stage == RoundStage.writing:
            game_round.stage = RoundStage.selecting
            game_round.save()
        elif game_round.stage == RoundStage.selecting:
            game_round.stage = RoundStage.answers
            game_round.save()
        elif game_round.stage == RoundStage.answers:
            next_round_number = Round.objects.filter(game=game_id, stage=RoundStage.finished).count() + 1
            players_cnt = len(get_players(game_id, host=False))
            if next_round_number >= players_cnt * game.cycles:
                game_round.stage = RoundStage.finished
                game.stage = GameStage.finished
                game.save()
            else:
                game_round.stage = RoundStage.results
            game_round.save()
        elif game_round.stage == RoundStage.results:
            game_round.stage = RoundStage.finished
            game_round.save()
            next_round_number = Round.objects.filter(game=game_id, stage=RoundStage.finished).count()
            players_cnt = len(get_players(game_id, host=False))
            if next_round_number % players_cnt:
                next_round = Round.objects.filter(game=game_id, stage=RoundStage.not_started).first()
                next_round.stage = RoundStage.writing
                next_round.save()
            else:
                game.stage = GameStage.preround
                game.save()
        logger.debug(f'round stage after: {game_round.stage}')
    logger.debug(f'game stage after: {game.stage}')


def upload_avatar(game_id: int, user: User, media: str) -> None:
    """ uploads player's avatar """

    player = user.player_set.get(game_id=game_id)
    if not player.avatar:
        media = media.replace('data:image/png;base64,', '')
        avatar = ContentFile(base64.b64decode(media), f'{game_id}_{player.nickname}.png')
        player.avatar = avatar
        player.save()
        logger.info(f'{player.nickname} uploaded avatar')
    else:
        raise ValidationError(f'{player.nickname} has already uploaded avatar')


def upload_painting(game_id: int, user: User, media) -> None:
    """ uploads player's painting """

    player = user.player_set.get(game_id=game_id)
    game_round = Round.objects.filter(game=game_id, painter=player, stage=RoundStage.not_started).first()
    if not game_round.painting:
        media = media.replace('data:image/png;base64,', '')
        painting = ContentFile(base64.b64decode(media), f'{game_id}_round_{game_round.order_number}_{player.nickname}.png')
        game_round.painting = painting
        game_round.save()
        logger.info(f'{player.nickname} uploaded painting for {game_round.order_number} round')
    else:
        raise ValidationError(f'{player.nickname} has already uploaded painting for {game_round.order_number} round')


def apply_variant(game_id: int, user: User, variant: str) -> None:
    """ applies player's variant """

    game_round = get_current_round(game_id)
    player = user.player_set.get(game_id=game_id)
    logger.info(f'{player.nickname} uploads painting')
    variant = variant.strip().lower()[:100]

    if not VARIANT_VALIDATION_RX.match(variant):
        raise ValidationError('Variant contains words of letters from mixed alphabets')
    if not Variant.objects.filter(game_round=game_round, author=player).exists():
        existing_variants = Variant.objects.filter(game_round=game_round).values_list('text', flat=True)
        for v in existing_variants:
            ratio = fuzz.ratio(variant, v)
            logger.debug(f'Compare "{variant}" with "{v}": ratio is {ratio}')
            if ratio >= MIN_SIMILARITY_RANK:
                raise ValidationError('Variant is similar to existing variants')
        Variant.objects.create(
            text=variant,
            game_round=game_round,
            author=player
        )
        logger.info(f'{player.nickname} applied variant for {game_round.order_number} round')
    else:
        logger.info(f'{player.nickname} has already applied variant for {game_round.order_number} round')


def select_variant(game_id: int, user: User, answer) -> None:
    """ applies which variant player has chosen"""

    game_round = get_current_round(game_id)
    player = user.player_set.get(game_id=game_id)
    if not Variant.objects.filter(game_round=game_round, selected_by=player).exists():
        variant = Variant.objects.get(game_round=game_round, text=answer)
        variant.selected_by.add(player)
        logger.info(f'{player.nickname} selected variant {variant.text}')
    else:
        raise ValidationError(f'{player.nickname} has already selected variant')


def calculate_results(game_id: int) -> None:
    """ calculates player's points and increment after round """

    current_round = get_current_round(game_id)
    Result.objects.select_for_update().filter(game=game_id).update(round_increment=0)
    variants = Variant.objects.filter(game_round=current_round)

    for variant in variants:
        if variant.author == current_round.painter:
            Result.objects.select_for_update().filter(
                game=game_id,
                player=variant.author
            ).update(
                result=F('result') + POINTS_FOR_CORRECT_RECOGNITION * variant.selected_by.all().count(),
                round_increment=F('round_increment') + POINTS_FOR_CORRECT_RECOGNITION * variant.selected_by.all().count()
            )
            Result.objects.select_for_update().filter(
                game=game_id,
                player__in=variant.selected_by.all()
            ).update(
                result=F('result') + POINTS_FOR_CORRECT_ANSWER,
                round_increment=F('round_increment') + POINTS_FOR_CORRECT_ANSWER
            )
        else:
            Result.objects.select_for_update().filter(game=game_id, player=variant.author).update(
                result=F('result') + POINTS_FOR_RECOGNITION * variant.selected_by.all().count(),
                round_increment=F('round_increment') + POINTS_FOR_RECOGNITION * variant.selected_by.all().count())

    logger.info('results are updated')


def stage_completed(game_id: int, game_stage: GameStage, round_stage: RoundStage) -> bool:
    """ checks if current game stage is completed"""

    players_cnt = Player.objects.filter(game_id=game_id, is_host=False).count()
    if game_stage == GameStage.preround:
        return Round.objects.filter(
            game=game_id,
            stage=RoundStage.not_started,
        ).exclude(
            painting__exact=''
        ).count() == players_cnt
    if game_stage == GameStage.round:
        current_round = get_current_round(game_id)
        if round_stage == RoundStage.writing:
            return Variant.objects.filter(
                game_round=current_round
            ).count() == players_cnt
        if round_stage == RoundStage.selecting:
            return Variant.objects.filter(
                game_round=current_round
            ).aggregate(Count('selected_by'))['selected_by__count'] == players_cnt - 1
    return False


def is_game_paused(game_id: int) -> bool:
    """ checks if game is paused"""

    return Game.objects.filter(pk=game_id, is_paused=True).exists()


def switch_pause_state(game_id: int, pause: bool) -> None:
    """ updates game state; """

    if pause:
        Game.objects.filter(pk=game_id).update(is_paused=True)
    else:
        Game.objects.filter(pk=game_id).update(is_paused=False)


def finish_game(game_id: int) -> None:
    """ change game status to finished """

    Game.objects.filter(pk=game_id).update(stage=GameStage.finished)


def get_players_answers(game_round: Round):
    answers = {
        'incorrect': [],
        'correct': None
    }
    variants = Variant.objects.filter(
        ~Q(selected_by=None) | Q(author=game_round.painter),
        game_round=game_round)
    for variant in variants:
        answer = {
            'text': variant.text,
            'author': {
                'nickname': variant.author.nickname if variant.author else 'Random answer',
                'avatar': variant.author.avatar.url if variant.author else None,
            },
            'selected_by': [
                {"nickname": player.nickname, "avatar": player.avatar.url}
                for player in variant.selected_by.all()
            ]
        }
        if variant.author == game_round.painter:
            answers['correct'] = answer
        else:
            answers['incorrect'].append(answer)
    return answers


def populate_missing_variants(game_round: Round):
    player_variants_num = game_round.round_variants.count()
    players_number = game_round.game.players.exclude(is_host=True).count()
    missing_answers = players_number - player_variants_num
    logger.info(f'generate {missing_answers} auto answers')
    if missing_answers:
        Variant.objects.bulk_create([
            Variant(
                game_round=game_round,
                text=auto_answer.strip().lower(),
                author=None,
            )
            for auto_answer in get_auto_answers(game_round.game.language, missing_answers)
        ])


def is_host(game_id: int, user: User) -> bool:
    return Player.objects.filter(game_id=game_id, user=user, is_host=True).exists()


def get_host_channel(game_id: int) -> str:
    return Player.objects.get(game_id=game_id, is_host=True).channel_name
