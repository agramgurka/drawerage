# Generated by Django 4.1.4 on 2023-03-04 15:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import application.services.basics


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=16)),
                ('text', models.TextField(unique=True)),
                ('source', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, verbose_name='code')),
                ('cycles', models.IntegerField(default=2, verbose_name='number of cycles')),
                ('stage', models.CharField(choices=[(application.services.basics.GameStage['pregame'], 'pregame'), (application.services.basics.GameStage['preround'], 'preround'), (application.services.basics.GameStage['round'], 'round'), (application.services.basics.GameStage['finished'], 'finished')], default=application.services.basics.GameStage['pregame'], max_length=20, verbose_name='game stage')),
                ('is_paused', models.BooleanField(default=False, verbose_name='is paused')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_host', models.BooleanField(verbose_name='is player a host')),
                ('nickname', models.CharField(max_length=100, null=True, verbose_name='nickname')),
                ('avatar', models.ImageField(upload_to='')),
                ('channel_name', models.CharField(default=None, max_length=100, null=True, verbose_name='ws channel name')),
                ('drawing_color', models.CharField(max_length=7, null=True, verbose_name='drawing color')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.IntegerField(verbose_name='round order number')),
                ('painting_task', models.CharField(max_length=1000, verbose_name='painting task')),
                ('painting', models.ImageField(upload_to='')),
                ('stage', models.CharField(choices=[(application.services.basics.RoundStage['not_started'], 'not started'), (application.services.basics.RoundStage['writing'], 'writing'), (application.services.basics.RoundStage['selecting'], 'selecting'), (application.services.basics.RoundStage['answers'], 'answers'), (application.services.basics.RoundStage['results'], 'results'), (application.services.basics.RoundStage['finished'], 'finished')], default=application.services.basics.RoundStage['not_started'], max_length=20, verbose_name='round stage')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_rounds', to='application.game')),
                ('painter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='painting_rounds', to='application.player')),
            ],
            options={
                'ordering': ['game', 'order_number'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=16)),
                ('text', models.TextField(unique=True)),
                ('source', models.CharField(blank=True, max_length=255)),
                ('up_vote', models.IntegerField(default=0)),
                ('down_vote', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=100, verbose_name='variant text')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player_variants', to='application.player')),
                ('game_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='round_variants', to='application.round')),
                ('selected_by', models.ManyToManyField(related_name='variants', to='application.player')),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.IntegerField(default=0, verbose_name="player's result")),
                ('round_increment', models.IntegerField(default=0, verbose_name='round increment')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.game')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.player')),
            ],
            options={
                'ordering': ['game', '-result'],
            },
        ),
        migrations.AddField(
            model_name='game',
            name='players',
            field=models.ManyToManyField(related_name='games', to='application.player'),
        ),
    ]
