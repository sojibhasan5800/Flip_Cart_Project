<h1 align="center">🛒 Flip-Cart E-Commerce Website</h1>
<h3 align="center">A Secure & Scalable E-Commerce Platform Built with Django</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/Django-4.x-green?logo=django" />
  <img src="https://img.shields.io/badge/DRF-REST%20API-red?logo=django" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql" />
  <img src="https://img.shields.io/badge/Redis-Celery-orange?logo=redis" />
</p>

<hr/>

## 🚀 Project Overview
Flip-Cart is a **secure, scalable, and user-friendly e-commerce platform** that ensures a seamless shopping experience.  
It focuses on **performance, data integrity, and security**, making it suitable for real-world deployment.

---

## ✨ Key Features
- 🔐 **User Registration & Authentication** → Email verification, secure login, password reset.  
- 🛒 **Personalized Cart Management** → Add/update products with real-time stock checks.  
- 💳 **Order & Payment Processing** → Smooth checkout with payment gateway integration.  
- ⭐ **User Reviews** → Post & retrieve reviews via REST APIs.  
- 🔗 **API Integration** → Fetch & update product data dynamically from third-party APIs.  
- ⚙️ **Admin API Generator** → Auto-generate APIs for any model.  
- ♻️ **Cart Persistence** → User cart saved across sessions.  
- 📨 **Email Notifications** → Order confirmations, password reset, promotions.  
- 🧾 **Voucher PDF Download** → Auto-generated discount vouchers.  
- 🌀 **Asynchronous Tasks** → Redis + Celery for background jobs.  
- 📑 **API Docs** → Swagger UI + Postman Collection for easy API testing.  
- 🛡️ **Security** → Secure coding best practices to protect data & transactions.  

---

## 🛠️ Tech Stack
<p>
  <img src="https://img.shields.io/badge/Python-3.10-blue?logo=python" />
  <img src="https://img.shields.io/badge/Django-4.x-green?logo=django" />
  <img src="https://img.shields.io/badge/DRF-API-red?logo=django" />
  <img src="https://img.shields.io/badge/PostgreSQL-blue?logo=postgresql" />
  <img src="https://img.shields.io/badge/MySQL-blue?logo=mysql" />
  <img src="https://img.shields.io/badge/Redis-orange?logo=redis" />
  <img src="https://img.shields.io/badge/Celery-green?logo=celery" />
  <img src="https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap" />
  <img src="https://img.shields.io/badge/Git-black?logo=git" />
</p>

---

## ⚡ API Documentation
- 📖 Swagger API Docs → [View Swagger UI](https://your-swagger-link.com)  
- 🔬 Postman Collection → [Download Postman JSON](https://your-postman-link.com)  

*(Update links above when available)*

---

## 🏗️ How to Run Locally
1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/flip-cart.git
   cd flip-cart
   python -m venv venv
   source venv/bin/activate   # (Linux/Mac)
   venv\Scripts\activate      # (Windows)
   pip install -r requirements.txt
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   redis-server
   celery -A flipcart worker --pool=solo -l info
   python manage.py runserver
   Visit → http://127.0.0.1:8000/
   <p align="center"> <b>✨ Flip-Cart is a personal project demonstrating secure, scalable e-commerce features with focus on user experience & backend robustness ✨</b> </p> ```





