from django import forms

from .models import Language
from .services.basics import GAME_CODE_LEN, NICKNAME_LEN


class JoinGameForm(forms.Form):
    game_code = forms.CharField(max_length=GAME_CODE_LEN)
    player_nickname = forms.CharField(max_length=NICKNAME_LEN)

    game_code.widget.attrs.update({'class': 'form-control'})
    player_nickname.widget.attrs.update({'class': 'form-control'})


class CreateGameForm(forms.Form):
    host_nickname = forms.CharField(max_length=NICKNAME_LEN)
    language = forms.ChoiceField(choices=[])
    cycles = forms.IntegerField()

    language.widget.attrs.update({'class': 'form-select'})
    host_nickname.widget.attrs.update({'class': 'form-control'})
    cycles.widget.attrs.update({'class': 'form-control', 'min': '1', 'step': '1', 'value': '2'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].choices = [
            (x.code, x.name)
            for x in Language.objects.all()
        ]
