# استخدام نسخة بايثون رسمية
FROM python:3.11-slim

# تثبيت مترجم C++ (g++) وأدوات النظام الضرورية
RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المكتبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع بالكامل
COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]
