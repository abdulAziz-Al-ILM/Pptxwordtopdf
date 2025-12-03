# Bazaviy rasm: Pythonning Debian asosidagi yupqa versiyasi
FROM python:3.10-slim-bullseye

# Ishchi katalog
WORKDIR /app

# 1. Konvertatsiya uchun LibreOffice va kerakli fontlarni o'rnatish.
# Bu, fayllarning buzilmasdan PDF ga o'tishini ta'minlaydi.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-dejavu \
    procps \
    # Ba'zi tarmoq kutubxonalari uchun zarur
    libxext6 \
    libxrender1 \
    libxtst6 \
    # Locales ni to'g'irlash
    locales \
    && rm -rf /var/lib/apt/lists/*

# 2. Locales ni sozlash (soffice uchun muhim)
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# 3. Python kutubxonalarini o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Bot kodini nusxalash
COPY main.py .

# 5. Botni ishga tushirish (root emas, oddiy foydalanuvchi sifatida tavsiya etiladi)
# Oddiy foydalanuvchini yaratish
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Botni ishga tushirish
CMD ["python", "main.py"]
