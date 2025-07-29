from django.db import migrations

def create_free_plan(apps, schema_editor):
    Plan = apps.get_model('assinaturas', 'Plan')
    Plan.objects.get_or_create(
        name='free',
        defaults={
            'price': 0,
            'duration_days': 7
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('assinaturas', '0002_plan_alter_subscription_plan'),
    ]

    operations = [
        migrations.RunPython(create_free_plan),
    ] 