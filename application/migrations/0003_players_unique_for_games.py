# Generated by Django 4.1.4 on 2023-03-15 13:15

from django.db import migrations, models
import django.db.models.deletion


def migrate_players(apps, schema_editor):
    Player = apps.get_model('application', 'Player')
    for player in Player.objects.all():
        player.game_id = player.games.all().get().pk
        player.save()


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0002_add_language_model'),
    ]

    operations = [
        migrations.RenameField(
            model_name='game',
            old_name='players',
            new_name='players_old',
        ),
        migrations.AddField(
            model_name='player',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='players', to='application.game'),
            preserve_default=False,
        ),
        migrations.RunPython(
            migrate_players,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='player',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players',
                                    to='application.game'),
        ),
        migrations.RemoveField(
            model_name='game',
            name='players_old',
        ),
    ]