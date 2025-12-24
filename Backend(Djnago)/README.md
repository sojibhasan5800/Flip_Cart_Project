# Flip-Cart E-Commerce Website

A secure and scalable e-commerce platform built with Django. Flip-Cart provides a smooth shopping experience for users while ensuring data integrity, security, and high performance.

---

## Project Overview

Flip-Cart is a **user-friendly and robust e-commerce application** designed for real-world use.  
It allows users to **browse products, add them to a cart, place orders, and make payments** securely.  
The platform handles **inventory management, order processing, and notifications** efficiently, making it suitable for small to medium online businesses.  
Admins can manage products, orders, and users easily, while developers can extend the system using REST APIs.  
Overall, Flip-Cart demonstrates **best practices in secure coding, scalable architecture, and modern web development**.

---

## Key Features

- **User Registration & Authentication**: Email verification, secure login, and password reset.  
- **Personalized Cart Management**: Add or update products with real-time stock checks.  
- **Order & Payment Processing**: Smooth checkout with integrated payment gateway.  
- **User Reviews**: Post and view product reviews via REST APIs.  
- **API Integration**: Fetch and update product data dynamically from third-party APIs.  
- **Admin API Generator**: Auto-generate APIs for any model in the backend.  
- **Cart Persistence**: User cart is saved across sessions.  
- **Email Notifications**: Automatic emails for order confirmation, promotions, and password resets.  
- **Voucher PDF Download**: Generate discount vouchers for orders.  
- **Asynchronous Tasks**: Background jobs handled via Redis + Celery.  
- **API Documentation**: Swagger UI and Postman Collection for testing and integration.  
- **Security**: Follows best practices to protect user data and transactions.

---

## Tech Stack

- **Backend**: Python 3.10+, Django 4.x, Django REST Framework, Celery, Redis  
- **Database**: PostgreSQL or MySQL  
- **Frontend**: Bootstrap 5 (responsive UI)  
- **Tools**: Git for version control, Swagger/Postman for API testing  

---

## ⚡ API Documentation
- 📖 Swagger API Docs → [View Swagger UI](https://your-swagger-link.com)  
- 🔬 Postman Collection → [Download Postman JSON](https://your-postman-link.com)  
---

## How to Run Locally

Follow these steps to set up the project on your local machine:

```bash
# Clone the repository
git clone https://github.com/your-username/flip-cart.git
cd flip-cart

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Linux / Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser

# Start Redis server
redis-server

# Start Celery worker for background tasks
celery -A flipcart worker --pool=solo -l info

# Run Django development server
python manage.py runserver
Visit → http://127.0.0.1:8000/

  

 Flip-Cart is a personal project demonstrating secure, scalable e-commerce features with focus on user experience & backend robustness ```





