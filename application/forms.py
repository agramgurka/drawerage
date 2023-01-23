from django import forms


class JoinGameForm(forms.Form):
    game_code = forms.CharField(max_length=10)
    player_nickname = forms.CharField(max_length=100)

    game_code.widget.attrs.update({'class': 'form-control'})
    player_nickname.widget.attrs.update({'class': 'form-control'})
