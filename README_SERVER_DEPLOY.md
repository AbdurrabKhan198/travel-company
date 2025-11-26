# 🚀 Server Deployment - One Command Setup

## GitHub Repository
**https://github.com/AbdurrabKhan198/travel-company.git**

---

## 📋 Steps:

### Step 1: GitHub पर Script Push करें

1. `deploy_on_server.sh` file को GitHub पर push करें
2. Ya phir server par directly upload करें

### Step 2: Server पर Run करें

```bash
# Server par SSH karein
ssh safar@165.232.178.54

# Script download karein (agar GitHub se)
wget https://raw.githubusercontent.com/AbdurrabKhan198/travel-company/main/deploy_on_server.sh

# Ya phir agar already hai, to:
cd /var/www/safarzonetravels  # ya kisi bhi directory mein
bash deploy_on_server.sh
```

**Ya phir ek hi command mein:**

```bash
# Root user se (recommended)
sudo bash <(curl -s https://raw.githubusercontent.com/AbdurrabKhan198/travel-company/main/deploy_on_server.sh)

# Ya phir safar user se
bash <(curl -s https://raw.githubusercontent.com/AbdurrabKhan198/travel-company/main/deploy_on_server.sh)
```

---

## ✅ यह Script Automatically करेगी:

1. ✅ System packages update करेगी
2. ✅ Python, Nginx, PostgreSQL install करेगी
3. ✅ Project directory बनाएगी
4. ✅ GitHub से code clone करेगी
5. ✅ Virtual environment setup करेगी
6. ✅ Dependencies install करेगी
7. ✅ Database migrations run करेगी
8. ✅ Static files collect करेगी
9. ✅ Gunicorn service setup करेगी
10. ✅ Nginx configure करेगी
11. ✅ Services start करेगी
12. ✅ Website live कर देगी!

---

## 🎯 Usage:

### First Time Deployment:

```bash
# Server par SSH karein
ssh safar@165.232.178.54

# Script run karein
bash deploy_on_server.sh
```

### Update (Agar code update karna hai):

```bash
# Server par
cd /var/www/safarzonetravels
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## 📝 Important Notes:

1. **Root Access:** Script ko root ya sudo access chahiye
2. **GitHub:** Code GitHub par hona chahiye
3. **Internet:** Server par internet connection hona chahiye
4. **DNS:** Domain ka DNS 165.232.178.54 par point hona chahiye

---

## 🔧 After Deployment:

### Create Superuser:
```bash
cd /var/www/safarzonetravels
source venv/bin/activate
python manage.py createsuperuser
```

### Setup SSL:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com
```

### Check Status:
```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## 🆘 Troubleshooting:

### Service Not Running:
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### View Logs:
```bash
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
```

### Permission Issues:
```bash
sudo chown -R safar:safar /var/www/safarzonetravels
```

---

## ✅ Checklist:

- [ ] Script GitHub par push ho gaya
- [ ] Server par script run kiya
- [ ] Website live hai (http://safarzonetravels.com)
- [ ] Superuser create kiya
- [ ] SSL setup kiya (optional)

---

**बस इतना ही! एक command se sab ho jayega! 🎉**

