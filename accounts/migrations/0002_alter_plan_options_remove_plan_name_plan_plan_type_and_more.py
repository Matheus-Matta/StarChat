# Generated by Django 4.2.23 on 2025-07-22 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='plan',
            options={'verbose_name': 'Plano', 'verbose_name_plural': 'Planos'},
        ),
        migrations.RemoveField(
            model_name='plan',
            name='name',
        ),
        migrations.AddField(
            model_name='plan',
            name='plan_type',
            field=models.CharField(choices=[('free', 'Gratuito'), ('premium', 'Premium'), ('master', 'Master')], default='free', max_length=20, verbose_name='Tipo de Plano'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='description',
            field=models.TextField(blank=True, verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Preço'),
        ),
    ]
