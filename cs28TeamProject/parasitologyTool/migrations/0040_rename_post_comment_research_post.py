# Generated by Django 3.2.9 on 2022-02-10 17:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parasitologyTool', '0039_auto_20220209_1947'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='post',
            new_name='research_post',
        ),
    ]
