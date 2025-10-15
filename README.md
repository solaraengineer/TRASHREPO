# Solara 🌐

A production-ready Django web application with API authentication, session handling, and frontend dynamic integration. Built for scale, security, and extendability.

---

## 🚀 Tech Stack

- **Backend:** Python 3.11+ · Django
- **Frontend:** HTML · CSS · JavaScript (Vanilla)
- **Authentication:** JWT (Access/Refresh Tokens), 2FA Email Verification
- **Database:** SQLite (development), PostgreSQL-ready
- **Hosting:** AWS EC2 + Cloudflare (DNS / CDN / SSL)
- **Security:** reCAPTCHA v2 · JWT-based Auth · Session Cookies
- **File Serving:** Static HTML via R2 / Cloudflare · Django API backend

---

## 📦 Project Structure

---

## 🛡 Features

- ✅ **User Registration & Login**
- ✅ **Email-based 2FA (code verification)**
- ✅ **JWT Authentication (Access + Refresh tokens)**
- ✅ **Session support (cookies, server-side verification)**
- ✅ **reCAPTCHA validation**
- ✅ **Custom User model ready for production**
- ✅ **Frontend-ready API endpoints**
- ✅ **Cloudflare + R2 support**

---

## 🧪 Setup Instructions

### 1. Clone the Repository

git clone https://github.com/solaraengineer/Renderpage.git

### 2. install dependecies 

pip install -r requirements.txt

### 3. Configure ur own .env file

### 4. Run migrations 
python manage.py migrate

### 5. Run server to test
python manage.py runserver

🔐 API Endpoints
	•	POST /api/register/ → Create account (reCAPTCHA protected)
	•	POST /api/register/verify/ → Submit email code (sets session)
	•	POST /api/login/ → Send 2FA code to email
	•	POST /api/login/verify/ → Get JWT access & refresh tokens
	•	POST /api/user/ → Get authenticated user data

    🌍 Deployment Notes
	•	Frontend is served from Cloudflare R2 or S3 bucket.
	•	Backend is deployed via AWS EC2 instance (Gunicorn + NGINX).
	•	Secure HTTPS is managed through Cloudflare (SSL Flexible or Full).
⸻
🔧 Customization
	•	Want to store more user data? Extend models.User.
	•	Replace SQLite with PostgreSQL for production.
	•	Swap out email for phone/SMS verification if needed.
	•	Add more endpoints for Paragraph or custom features.





