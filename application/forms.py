from django import forms
from .services.basics import GAME_CODE_LEN, NICKNAME_LEN


class JoinGameForm(forms.Form):
    game_code = forms.CharField(max_length=GAME_CODE_LEN)
    player_nickname = forms.CharField(max_length=NICKNAME_LEN)

    game_code.widget.attrs.update({'class': 'form-control'})
    player_nickname.widget.attrs.update({'class': 'form-control'})
