# ---------- Base Image ----------
FROM python:3.10-slim

# ---------- Environment Variables ----------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ---------- Working Directory ----------
WORKDIR /app

# ---------- Copy Project Files ----------
COPY . /app/

# ---------- Install Dependencies ----------
# RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ---------- Expose Port ----------
EXPOSE 8000

# ---------- Run Django (Localhost Mode) ----------
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000", "python manage.py search_index --rebuild"]

# ---------- NOTE ----------
#  Deployment time, replace CMD with:
# CMD ["gunicorn", "flipcart_project.wsgi:application", "--bind", "0.0.0.0:8000"]
