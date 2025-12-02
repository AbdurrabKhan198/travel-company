# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travels', '0015_userprofile_aadhar_card_company_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='company_name',
            field=models.CharField(blank=True, help_text='Name of your company', max_length=200, verbose_name='company name'),
        ),
    ]

