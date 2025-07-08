FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instala Python, pip, wkhtmltopdf y dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    wkhtmltopdf \
    xfonts-75dpi xfonts-base fontconfig libxrender1 libxext6 libx11-6 \
    gcc g++ libffi-dev libssl-dev \
    libxml2-dev libxslt1-dev libjpeg-dev libpng-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev \
    libharfbuzz-dev libfribidi-dev libxcb1-dev pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && which wkhtmltopdf \
    && wkhtmltopdf --version

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
