# Generated by Django 4.1 on 2022-11-27 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrador', '0010_alter_chamado_data_conclusao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chamado',
            name='data_conclusao',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]