============================================
  Safar Zone Travels - Deployment Guide
============================================

DOMAIN: safarzonetravels.com
IP: 165.232.178.54

QUICK START (Windows):
---------------------
1. Double-click: deploy.bat
   - This prepares your project for deployment
   - Installs dependencies
   - Runs migrations
   - Collects static files

2. Double-click: production_start.bat
   - This starts the production server
   - Uses Gunicorn on port 8000

FOR DIGITALOCEAN SERVER:
------------------------
1. Upload all project files to your server
2. SSH into your server
3. Run the deployment commands (see DEPLOYMENT_GUIDE.md)
4. Configure Nginx and Gunicorn
5. Set up SSL certificate

IMPORTANT NOTES:
----------------
- Make sure DNS is pointing to 165.232.178.54
- Set DEBUG=False in production
- Configure proper SECRET_KEY
- Set up SSL/HTTPS
- Configure firewall

For detailed instructions, see: DEPLOYMENT_GUIDE.md

