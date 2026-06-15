FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    vim \
    nano \
    less \
    procps \
    htop \
    net-tools \
    iputils-ping \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -s /bin/bash yuna && chown -R yuna:yuna /app

EXPOSE 8080

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

CMD ["python", "main.py"]
