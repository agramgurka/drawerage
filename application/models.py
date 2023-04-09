from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from .services.basics import GameStage, RoundStage


class LanguageManager(models.Manager):
    def get_by_natural_key(self, language_code):
        return self.get(code=language_code)


class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255, unique=True)

    objects = LanguageManager()

    def natural_key(self):
        return (self.code, )

    def __str__(self):
        return self.name


class Game(models.Model):
    """ games """

    language = models.ForeignKey(Language, related_name='games', on_delete=models.CASCADE)
    code = models.CharField('code', max_length=10)
    cycles = models.IntegerField('number of cycles', default=2)
    stage = models.CharField(
        'game stage',
        max_length=20,
        choices=[(stage, stage.value) for stage in GameStage],
        default=GameStage.pregame
    )
    is_paused = models.BooleanField('is paused', default=False)

    def __str__(self):
        return f'Game {self.code}, lang: {self.language.code}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=~Q(stage=GameStage.finished),
                name='unique_active_game_code'
            )
        ]


class Player(models.Model):
    """ player's account """

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    game = models.ForeignKey(Game, related_name='players', on_delete=models.CASCADE)
    is_host = models.BooleanField('is player a host')
    nickname = models.CharField('nickname', max_length=100, null=True)
    avatar = models.ImageField(upload_to='')
    channel_name = models.CharField('ws channel name', max_length=100, null=True, default=None)
    drawing_color = models.CharField('drawing color', max_length=7, null=True)

    def __str__(self):
        return self.nickname or '<HOST>'


class Round(models.Model):
    """ games' rounds """

    game = models.ForeignKey(Game, related_name='game_rounds', on_delete=models.CASCADE)
    order_number = models.IntegerField('round order number')
    painter = models.ForeignKey(Player, related_name='painting_rounds', null=True, on_delete=models.SET_NULL)
    painting_task = models.CharField('painting task', max_length=1000)
    painting = models.ImageField()
    stage = models.CharField(
        'round stage',
        max_length=20,
        choices=[(stage, stage.value) for stage in RoundStage],
        default=RoundStage.not_started
    )

    class Meta:
        ordering = ['game', 'order_number']


class Variant(models.Model):
    """ rounds' variants """

    text = models.CharField('variant text', max_length=100)
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, blank=True, null=True, related_name='used_variants')
    game_round = models.ForeignKey(Round, related_name='round_variants', on_delete=models.CASCADE)
    author = models.ForeignKey(Player, related_name='player_variants', null=True, on_delete=models.SET_NULL)
    selected_by = models.ManyToManyField(Player, related_name='variants')
    liked_by = models.ManyToManyField(Player, related_name='liked_variants')


class Result(models.Model):
    """ games' results """

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    result = models.IntegerField('player\'s result', default=0)
    round_increment = models.IntegerField('round increment', default=0)

    class Meta:
        ordering = ['game', '-result']

    def as_dict(self):
        return {
            'player__avatar': self.player.avatar.url,
            'player__nickname': self.player.nickname,
            'player__drawing_color': self.player.drawing_color,
            'result': self.result,
            'round_increment': self.round_increment,
        }


class Task(models.Model):
    language = models.ForeignKey(Language, related_name='tasks', on_delete=models.CASCADE)
    text = models.TextField(unique=True)
    source = models.CharField(max_length=255, blank=True)
    auto_created = models.BooleanField(default=False)
    up_vote = models.IntegerField(default=0)
    down_vote = models.IntegerField(default=0)

    @property
    def prepared_text(self):
        return self.text.lower().strip()


class AutoAnswer(models.Model):
    language = models.ForeignKey(Language, related_name='auto_answers', on_delete=models.CASCADE)
    text = models.TextField(unique=True)
    source = models.CharField(max_length=255, blank=True)
