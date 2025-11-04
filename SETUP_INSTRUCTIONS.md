# 🛫 Safar Zone Travels - Setup Instructions

A modern Django 5+ travel and tours booking platform with Tailwind CSS.

## 📋 Features

- ✅ Flight search with admin-controlled inventory dates
- ✅ User authentication (Login/Signup)
- ✅ Booking system with passenger details
- ✅ User dashboard with booking history
- ✅ Admin panel for inventory and package management
- ✅ Responsive design with Tailwind CSS
- ✅ Beautiful UI with animations

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+ (for Tailwind CSS)
- pip (Python package manager)

### Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd Travel_agency

# Install required packages
pip install -r requirements.txt
```

### Step 2: Install Tailwind CSS

```bash
# Install Tailwind CSS via npm
npm install

# Build Tailwind CSS (one-time build)
npm run build:css

# OR watch for changes during development
npm run watch:css
```

### Step 3: Database Setup

```bash
# Run migrations to create database tables
python manage.py makemigrations
python manage.py migrate

# Populate sample data (routes, inventory, packages, users)
python manage.py populate_sample_data
```

### Step 4: Run the Development Server

```bash
# Start Django development server
python manage.py runserver
```

Visit: **http://localhost:8000**

## 👤 Test Credentials

After running `populate_sample_data`, you can login with:

### Admin User (Staff Access)
- **Username:** admin
- **Password:** admin123
- **Access:** Full admin panel + inventory management

### Regular User
- **Username:** testuser
- **Password:** test123
- **Access:** Booking and dashboard

## 📁 Project Structure

```
Travel_agency/
├── Travel_agency/          # Main project settings
│   ├── settings.py         # Django settings
│   └── urls.py             # Main URL routing
├── travels/                # Main app
│   ├── models.py           # Database models (Route, Inventory, Booking, Package)
│   ├── views.py            # View functions
│   ├── admin.py            # Admin configuration
│   ├── urls.py             # App URL routing
│   └── management/         # Custom commands
│       └── commands/
│           └── populate_sample_data.py
├── templates/              # HTML templates
│   ├── base.html           # Base template with navbar/footer
│   ├── index.html          # Homepage
│   ├── search.html         # Flight search results
│   ├── booking.html        # Booking form
│   ├── dashboard.html      # User dashboard
│   ├── login.html          # Login page
│   ├── signup.html         # Signup page
│   ├── admin_inventory.html # Admin inventory management
│   └── admin_packages.html  # Admin package management
├── static/
│   ├── css/
│   │   └── output.css      # Compiled Tailwind CSS (auto-generated)
│   ├── src/
│   │   └── input.css       # Tailwind source file
│   └── js/
│       └── main.js         # JavaScript functionality
├── tailwind.config.js      # Tailwind configuration
├── package.json            # Node dependencies
├── requirements.txt        # Python dependencies
└── manage.py               # Django management script
```

## 🎯 Key Functionalities

### User Flow
1. **Search Flights** - Select origin, destination, and date
2. **View Results** - See available flights with prices
3. **Book Flight** - Enter passenger details and confirm
4. **View Dashboard** - Manage bookings (view, print, cancel)

### Admin Flow
1. **Manage Routes** - Add/edit flight routes via Django admin
2. **Manage Inventory** - Add available dates and ticket prices
3. **Manage Packages** - Create featured travel packages for homepage
4. **View Bookings** - Monitor all user bookings

## 🛠️ Development Commands

### Build Tailwind CSS

```bash
# One-time build (production)
npm run build:css

# Watch mode (development)
npm run watch:css
```

### Django Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser (alternative to sample data)
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Populate sample data
python manage.py populate_sample_data
```

## 📊 Sample Data Included

After running `populate_sample_data`:

- **10 Flight Routes** (Mumbai-Delhi, Delhi-Goa, etc.)
- **60+ Inventory Items** (Available dates for next 30 days)
- **6 Travel Packages** (Goa, Kerala, Rajasthan, Himachal, Dubai, Maldives)
- **2 Users** (admin and testuser)

## 🎨 Design Features

- **Modern Sky Gradient** hero section
- **Animated Plane Icons** on homepage
- **Responsive Navigation** with mobile menu
- **Card-based Layouts** for packages and bookings
- **Auto-dismissing Alerts** for notifications
- **Print-friendly** booking pages
- **Smooth Transitions** and hover effects

## 🔧 Customization

### Add New Routes
1. Login as admin: http://localhost:8000/admin
2. Navigate to Routes section
3. Add new route with flight number, origin, destination

### Add Inventory
1. Login as admin
2. Visit: http://localhost:8000/admin/inventory/
3. Select route, date, price, and seats
4. Submit to make available for booking

### Add Travel Packages
1. Login as admin
2. Visit: http://localhost:8000/admin/packages/
3. Fill in destination, title, description, price
4. Add image URL (optional)
5. Mark as featured to show on homepage

## 🚦 Workflow

### User Booking Process
```
Homepage → Search → Results → Login → Booking Form → Confirmation → Dashboard
```

### Date Availability
- Only dates added by admin in inventory are selectable
- Past dates are automatically disabled
- Seats decrease as bookings are made
- Cancelled bookings return seats to inventory

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop (1920px+)
- Laptop (1024px - 1920px)
- Tablet (768px - 1024px)
- Mobile (320px - 768px)

## 🐛 Troubleshooting

### Tailwind CSS Not Loading
```bash
# Rebuild Tailwind CSS
npm run build:css
```

### Static Files Not Found
```bash
# Collect static files
python manage.py collectstatic
```

### Database Errors
```bash
# Reset database
python manage.py flush
python manage.py migrate
python manage.py populate_sample_data
```

## 🔐 Security Notes

- Change `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Configure proper `ALLOWED_HOSTS`
- Use environment variables for sensitive data
- Never commit sensitive credentials

## 📝 Tech Stack

- **Backend:** Django 5.2+
- **Frontend:** HTML5, Vanilla JavaScript
- **Styling:** Tailwind CSS 3.4
- **Icons:** Font Awesome 6
- **Database:** SQLite (development) - PostgreSQL ready
- **Authentication:** Django built-in auth system

## 🎯 Production Deployment

For production deployment:

1. Set environment variables
2. Configure PostgreSQL database
3. Set `DEBUG = False`
4. Configure `ALLOWED_HOSTS`
5. Set up static file serving (WhiteNoise or CDN)
6. Use proper secret key
7. Enable HTTPS
8. Configure email backend for notifications

## 📞 Support

For issues or questions:
- Check Django documentation: https://docs.djangoproject.com
- Check Tailwind documentation: https://tailwindcss.com/docs

---

**Built with ❤️ for Safar Zone Travels**
