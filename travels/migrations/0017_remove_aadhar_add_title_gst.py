# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travels', '0016_userprofile_company_name'),
    ]

    operations = [
        # Remove aadhar_number field
        migrations.RemoveField(
            model_name='userprofile',
            name='aadhar_number',
        ),
        # Remove company_logo field
        migrations.RemoveField(
            model_name='userprofile',
            name='company_logo',
        ),
        # Add title field
        migrations.AddField(
            model_name='userprofile',
            name='title',
            field=models.CharField(choices=[('Mr', 'Mr'), ('Mrs', 'Mrs'), ('Miss', 'Miss'), ('Ms', 'Ms'), ('Dr', 'Dr')], default='Mr', max_length=10, verbose_name='title'),
        ),
        # Add gst_number field
        migrations.AddField(
            model_name='userprofile',
            name='gst_number',
            field=models.CharField(blank=True, help_text='GST number (Optional)', max_length=15, null=True, unique=True, verbose_name='GST Number'),
        ),
        # Note: aadhar_card field is kept (not removed) as it's still required
    ]

