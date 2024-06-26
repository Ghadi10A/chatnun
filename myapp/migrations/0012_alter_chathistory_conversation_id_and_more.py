# Generated by Django 4.1.4 on 2023-05-18 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_alter_chathistory_conversation_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chathistory',
            name='conversation_id',
            field=models.CharField(default='e4573f05-227e-46d9-bd18-900252be9f47', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='emojireaction',
            name='emoji',
            field=models.CharField(choices=[('heart', '❤️'), ('thumbs_up', '👍'), ('thumbs_down', '👎'), ('angry', '😠'), ('smiling_face', '😊')], max_length=20),
        ),
    ]
