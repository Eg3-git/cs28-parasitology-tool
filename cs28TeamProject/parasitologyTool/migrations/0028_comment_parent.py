# Generated by Django 3.2.9 on 2022-02-09 12:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parasitologyTool', '0027_alter_comment_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parasitologyTool.comment'),
        ),
    ]