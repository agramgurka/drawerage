from django.contrib import admin

from .models import AutoAnswer, Game, Player, Round, Task
from .services.basics import GameStage


class RoundTabularAdmin(admin.TabularInline):
    model = Round
    extra = 0
    fields = ('order_number', 'painter', 'painting_task', 'painting', 'variants', 'stage')
    readonly_fields = ('variants',)

    def variants(self, obj: Round):
        return ', '.join(obj.round_variants.values_list('text', flat=True))


class PlayerTabularAdmin(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('code', 'language', 'player_num', 'is_finished')
    list_filter = ('stage', )
    inlines = (PlayerTabularAdmin, RoundTabularAdmin)
    search_fields = ('code__iexact', )

    def player_num(self, obj: Game):
        return obj.players.count()

    def is_finished(self, obj: Game):
        return obj.stage == GameStage.finished
    is_finished.boolean = True


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('text', 'language', 'source')
    list_filter = ('language', 'source')
    search_fields = ('text__icontains', )


@admin.register(AutoAnswer)
class AutoAnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'language', 'source')
    list_filter = ('language', 'source')
    search_fields = ('text__icontains', )
