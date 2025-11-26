# 🚀 Safar Zone Travels - Deployment Steps (हिंदी में)

## 📋 आपको क्या करना है:

### **सिर्फ 3 Steps:**

---

## ✅ **STEP 1: GitHub पर Code Push करें**

अगर आपका code पहले से GitHub पर है, तो skip करें।

अगर नहीं है, तो:

```bash
# Windows पर Git Bash या CMD खोलें
cd "C:\Users\hp\Desktop\clients\travel company\Travel_agency"

# Git initialize करें (अगर पहले नहीं किया)
git init
git add .
git commit -m "Deployment ready"

# GitHub repository add करें
git remote add origin https://github.com/AbdurrabKhan198/travel-company.git

# Code push करें
git branch -M main
git push -u origin main
```

---

## ✅ **STEP 2: Batch File Run करें**

1. **`auto_deploy.bat`** file को double-click करें
2. Username enter करें (default: root)
3. Password enter करें (जब पूछे)
4. बस wait करें... सब automatically हो जाएगा!

**यह file automatically करेगी:**
- ✅ सभी packages install करेगी
- ✅ Project directory बनाएगी
- ✅ GitHub से code clone करेगी
- ✅ Virtual environment setup करेगी
- ✅ Dependencies install करेगी
- ✅ Database migrations run करेगी
- ✅ Static files collect करेगी
- ✅ Gunicorn service start करेगी
- ✅ Nginx configure करेगी
- ✅ Website live कर देगी

---

## ✅ **STEP 3: SSL Certificate Setup (Optional लेकिन Recommended)**

```bash
# Server पर SSH करें
ssh root@165.232.178.54

# Certbot install करें
apt install -y certbot python3-certbot-nginx

# SSL certificate लें
certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com
```

---

## 🎯 **बस इतना ही!**

आपकी website अब live है:
- **http://safarzonetravels.com**
- **http://165.232.178.54**

---

## 📝 **Important Notes:**

1. **SSH Access:** आपके पास server का SSH access होना चाहिए
2. **Root Access:** Initial setup के लिए root access चाहिए
3. **GitHub:** Code GitHub पर होना चाहिए
4. **DNS:** Domain का DNS 165.232.178.54 पर point होना चाहिए

---

## 🔄 **Future Updates (Code Update करने के लिए):**

### Windows पर:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Server पर (automated update script):
```bash
ssh safar@165.232.178.54 "cd /var/www/safarzonetravels && git pull && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && sudo systemctl restart gunicorn"
```

या फिर **`update_site.bat`** file run करें (नीचे दी गई है)

---

## 🆘 **अगर कुछ Problem हो:**

### 1. SSH Connection Error
```bash
# Check करें SSH working है या नहीं
ssh root@165.232.178.54
```

### 2. Permission Error
```bash
# Server पर run करें
sudo chown -R safar:safar /var/www/safarzonetravels
```

### 3. Service Not Running
```bash
# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx

# Restart करें
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 4. View Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## ✅ **Checklist:**

- [ ] Code GitHub पर push हो गया
- [ ] `auto_deploy.bat` run किया
- [ ] Website खुल रही है (http://safarzonetravels.com)
- [ ] SSL certificate setup किया (optional)
- [ ] Superuser create किया (admin panel के लिए)

---

## 🎉 **Success!**

आपकी website अब live है! 🚀

**Admin Panel:** http://safarzonetravels.com/admin

**Main Site:** http://safarzonetravels.com

