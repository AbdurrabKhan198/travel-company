# Generated migration for changing model names

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('travels', '0029_rename_executive_active_idx_salesrep_active_idx_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={
                'permissions': [
                    ('can_manage_bookings', 'Can manage bookings'),
                    ('can_manage_routes', 'Can manage routes'),
                    ('can_view_reports', 'Can view reports')
                ],
                'verbose_name': 'Admin',
                'verbose_name_plural': 'Admins'
            },
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={
                'verbose_name': 'Agency',
                'verbose_name_plural': 'Agencies'
            },
        ),
    ]
