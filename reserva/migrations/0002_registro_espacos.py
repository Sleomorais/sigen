# Generated by Django 4.1 on 2022-10-12 00:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reserva', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registro',
            name='espacos',
            field=models.CharField(choices=[('Espaço01', 'Espaço01'), ('Espaço02', 'Espaço02'), ('Espaço03', 'Espaço03')], default='', max_length=30),
            preserve_default=False,
        ),
    ]
