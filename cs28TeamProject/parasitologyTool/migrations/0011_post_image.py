# Generated by Django 3.2.9 on 2021-12-20 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parasitologyTool', '0010_remove_post_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(default=None, upload_to='clinical_pictures'),
        ),
    ]