# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travels', '0014_auto_20251126_0046'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='aadhar_card',
            field=models.ImageField(blank=True, help_text='Upload your Aadhar card image (Required)', null=True, upload_to='user_documents/aadhar/', verbose_name='Aadhar Card'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='company_logo',
            field=models.ImageField(blank=True, help_text='Upload your company logo (Optional)', null=True, upload_to='user_documents/company_logo/', verbose_name='Company Logo'),
        ),
    ]

