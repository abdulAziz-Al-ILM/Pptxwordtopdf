# Bazaviy rasm: Python va Debian (LibreOffice uchun qulay)
FROM python:3.10-slim-bullseye

# Ishchi katalog
WORKDIR /app

# Konvertatsiya uchun LibreOffice'ni o'rnatish
# Bullseye-da libreoffice-writer va libreoffice-calc o'rniga libreoffice-core kerak bo'lishi mumkin.
# Fontlar va boshqa yordamchi vositalarni o'rnatish
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-dejavu \
    procps \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Locales ni sozlash
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Python kutubxonalarini o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodini nusxalash
COPY main.py .

# LibreOffice-ning muammosiz ishlashi uchun zarur bo'lishi mumkin bo'lgan foydalanuvchini yaratish
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Botni ishga tushirish
CMD ["python", "main.py"]
