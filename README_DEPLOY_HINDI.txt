============================================
  Safar Zone Travels - Deployment Guide
  (हिंदी में - Step by Step)
============================================

🚀 QUICK START - सिर्फ 3 Steps:

STEP 1: GitHub पर Code Push करें
---------------------------------
अगर code पहले से GitHub पर है, तो skip करें।

अगर नहीं है:
1. Git Bash खोलें
2. Project folder में जाएं
3. Run करें:
   git init
   git add .
   git commit -m "Deployment"
   git remote add origin https://github.com/AbdurrabKhan198/travel-company.git
   git push -u origin main


STEP 2: Batch File Run करें
----------------------------
1. auto_deploy.bat file को double-click करें
2. Username enter करें (root)
3. Password enter करें
4. Wait करें... सब automatically हो जाएगा!

यह automatically करेगा:
✅ Packages install
✅ Code clone from GitHub
✅ Virtual environment setup
✅ Dependencies install
✅ Database setup
✅ Services start
✅ Website live!


STEP 3: SSL Setup (Optional)
-----------------------------
ssh root@165.232.178.54
apt install -y certbot python3-certbot-nginx
certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com


🎯 बस इतना ही!

आपकी website live है:
- http://safarzonetravels.com
- http://165.232.178.54


📝 Important Files:
-------------------
1. auto_deploy.bat          - पहली बार deployment के लिए
2. update_site.bat           - Code update करने के लिए
3. create_superuser.bat     - Admin user बनाने के लिए


🔄 Future Updates:
------------------
1. Code change करें
2. update_site.bat run करें
3. Done!


🆘 Help:
---------
अगर problem हो, तो:
- DEPLOYMENT_STEPS_HINDI.md देखें
- Server logs check करें
- SSH connection verify करें


✅ Checklist:
-------------
[ ] Code GitHub पर है
[ ] auto_deploy.bat run किया
[ ] Website खुल रही है
[ ] SSL setup किया (optional)
[ ] Superuser create किया


🎉 Success!

