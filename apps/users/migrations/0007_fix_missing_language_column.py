from django.db import migrations, connection

def add_language_column_if_needed(apps, schema_editor):
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE users_customusermodel ADD COLUMN IF NOT EXISTS language varchar(50) DEFAULT 'English';")

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_customusermodel_is_blocked'),
    ]

    operations = [
        migrations.RunPython(add_language_column_if_needed, migrations.RunPython.noop),
    ]

