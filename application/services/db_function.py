import base64
import random
from random import choices
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import F, Count
from django.http import HttpRequest
from django.core.files.base import ContentFile

from ..models import Player, Game, Round, Variant, Result
from .basics import (DrawingColors,
                     GameRole, GameStage, RoundStage,
                     POINTS_FOR_CORRECT_ANSWER,
                     POINTS_FOR_RECOGNITION,
                     POINTS_FOR_CORRECT_RECOGNITION,
                     GAME_CODE_LEN, USERNAME_LEN, CODE_CHARS,)
from .tasks import PredefinedTaskProducer, Restriction
from .utils import setup_logger

logger = setup_logger(__name__)


def generate_game_code(code_len=GAME_CODE_LEN) -> str:
    """ generates and returns unique shortcode for a game; """

    while True:
        code = ''.join(choices(CODE_CHARS, k=code_len))
        if not Game.objects.filter(code=code).exclude(stage=GameStage.finished).exists():
            return code


def generate_username(name_len=USERNAME_LEN):
    while True:
        new_username = ''.join(choices(population=CODE_CHARS, k=name_len))
        if not User.objects.filter(username=new_username).exists():
            return new_username


def create_user() -> User:
    """ creates new user object in database """

    user = User.objects.create_user(username=generate_username())
    return user


def register_channel(game_id: int, user: User, channel_name: str):
    """ registers player's websocket channel name"""

    Player.objects.filter(games=game_id, user=user).update(channel_name=channel_name)


def create_player(user: User, nickname: str = None, is_host: bool = False) -> Player:
    """ creates player's record """

    color = random.choices([color.value for color in DrawingColors])[0]

    return Player.objects.create(user=user, nickname=nickname, is_host=is_host, drawing_color=color)


def create_game(request, cycles=2) -> int:
    """ creates new game object and adds game's host to it """

    game = Game.objects.create(code=generate_game_code(), cycles=cycles)
    host = create_player(user=request.user, is_host=True)
    game.players.add(host)
    return game.pk


def get_player_color(game_id: int, user: User) -> str:
    """ returns player's drawing color """

    return Player.objects.get(games=game_id, user=user).drawing_color


def get_active_game(user: User) -> Optional[int]:
    """ returns id of player's/host's active game, if it exists"""

    if user.is_authenticated:
        active_games = Game.objects.filter(players__user=user).exclude(stage=GameStage.finished)
        if active_games:
            return active_games.first().pk
    return None


def get_game_code(game_id: int) -> str:
    """ returns game code """

    return Game.objects.get(pk=game_id).code


def join_game(request: HttpRequest, game_code: str, nickname: str) -> Optional[int]:
    """ if game exists, adds user to players; returns game id"""

    game = Game.objects.get(code=game_code.upper())
    if game.stage == GameStage.pregame:
        if not Player.objects.filter(user=request.user, games=game).exists():
            player = create_player(user=request.user, nickname=nickname)
            game.players.add(player)
        return game.pk


def create_drawing_task(restrictions) -> tuple[str, Restriction]:
    """ returns new painting task """

    return PredefinedTaskProducer().get_task(restrictions)
    # return "some unique painting task", []


def create_rounds(game_id: int) -> None:
    """ creates rounds for game """

    players = get_players(game_id)
    game = Game.objects.get(pk=game_id)
    restrictions = None
    for order_number, player in enumerate(players * game.cycles):
        task, restrictions = create_drawing_task(restrictions)
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
        return list(Player.objects.filter(games=game_id))
    return list(Player.objects.filter(games=game_id, is_host=False))


def get_game_stage(game_id: int) -> str:
    """ returns current game stage """

    return Game.objects.get(pk=game_id).stage


def get_role(user: User, game_id: int) -> Optional[GameRole]:
    """ returns player game role: player or host"""

    if Player.objects.filter(games=game_id, user=user, is_host=True).exists():
        return GameRole.host
    if Player.objects.filter(games=game_id, user=user, is_host=False).exists():
        return GameRole.player
    else:
        return None


def finished_painting(game: Game, player: Player) -> bool:
    """ returns True if player has finished painting task """

    return Round.objects.filter(
        game=game,
        painter=player,
        stage=RoundStage.not_started,
    ).exclude(
        painting__exact=''
    ).exists()


def get_drawing_task(game_id: int, player: Player) -> str:
    """ returns player's painting task for a cycle """

    return Round.objects.filter(
        game=game_id,
        painter=player,
        stage=RoundStage.not_started
    ).first().painting_task


def applied_variant(game_round: Round, player: Player) -> bool:
    """ returns True if player has applied variant for round's painting task """

    return Variant.objects.filter(game_round=game_round, author=player).exists()


def selected_variant(game_round: Round, player: Player) -> bool:
    """ returns True if player has selected variant """

    return Variant.objects.filter(
        game_round=game_round,
        selected_by=player
    ).exists() or game_round.painter == player


def get_variants(game_round: Round, player: Player) -> list:
    """ returns players' variants for a round """

    return list(Variant.objects.filter(game_round=game_round).exclude(author=player).order_by('?').values('text'))


def get_results(game: Game):
    """ returns game's results """

    return list(Result.objects.filter(game=game).values('player__nickname', 'result', 'round_increment'))


def next_stage(game_id: int):
    """ switch game stage """

    stage = Game.objects.get(pk=game_id).stage
    if stage == GameStage.pregame:
        Game.objects.filter(pk=game_id).update(stage=GameStage.preround)

    elif stage == GameStage.preround:
        Game.objects.filter(pk=game_id).update(stage=GameStage.round)
        next_round = Round.objects.filter(
            game=game_id,
            stage=RoundStage.not_started
        ).first()
        next_round.stage = RoundStage.writing
        next_round.save()

    elif stage == GameStage.round:
        if Round.objects.filter(stage=RoundStage.writing).exists():
            Round.objects.filter(stage=RoundStage.writing).update(stage=RoundStage.selecting)

        elif Round.objects.filter(stage=RoundStage.selecting).exists():
            Round.objects.filter(stage=RoundStage.selecting).update(stage=RoundStage.results)

        elif Round.objects.filter(stage=RoundStage.results).exists():
            Round.objects.filter(stage=RoundStage.results).update(stage=RoundStage.finished)
            next_round_number = Round.objects.filter(game=game_id, stage=RoundStage.finished).count()
            players_cnt = Player.objects.filter(games=game_id, is_host=False).count()
            if next_round_number % players_cnt:
                next_round = Round.objects.filter(
                    game=game_id,
                    stage=RoundStage.not_started
                ).first()
                next_round.stage = RoundStage.writing
                next_round.save()

            else:
                cycles = Game.objects.get(pk=game_id).cycles
                if next_round_number >= players_cnt * cycles:
                    Game.objects.filter(pk=game_id).update(stage=GameStage.finished)
                else:
                    Game.objects.filter(pk=game_id).update(stage=GameStage.preround)


def upload_avatar(game_id: int, user: User, media: str) -> None:
    """ uploads player's avatar """

    player = Player.objects.get(games=game_id, user=user)
    media = media.replace('data:image/png;base64,', '')
    avatar = ContentFile(base64.b64decode(media), f'{game_id}_{player.nickname}.png')
    player.avatar = avatar
    player.save()
    logger.info(f'{player.nickname} uploaded avatar')


def upload_painting(game_id: int, user: User, media) -> None:
    """ uploads player's painting """

    player = Player.objects.get(games=game_id, user=user)
    media = media.replace('data:image/png;base64,', '')
    game_round = Round.objects.filter(game=game_id, painter=player, stage=RoundStage.not_started).first()
    painting = ContentFile(base64.b64decode(media), f'{game_id}_round_{game_round.order_number}_{player.nickname}.png')
    game_round.painting = painting
    game_round.save()
    logger.info(f'{player.nickname} uploaded painting for {game_round.order_number} round')


def apply_variant(game_id: int, user: User, variant: str) -> None:
    """ applies player's variant """

    game_round = get_current_round(game_id)
    player = Player.objects.get(games=game_id, user=user)
    logger.info(f'{player.nickname} uploads painting')
    if not Variant.objects.filter(game_round=game_round, author=player).exists():
        Variant.objects.create(
            text=variant,
            game_round=game_round,
            author=player
        )
    logger.info(f'{player.nickname} applied variant for {game_round.order_number} round')


def select_variant(game_id: int, user: User, answer) -> None:
    """ applies which variant player has chosen"""

    game_round = get_current_round(game_id)
    player = Player.objects.get(games=game_id, user=user)
    variant = Variant.objects.get(game_round=game_round, text=answer)
    variant.selected_by.add(player)
    logger.info(f'{player.nickname} selected variant {variant.text}')


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

    players_cnt = Player.objects.filter(games=game_id, is_host=False).count()
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

