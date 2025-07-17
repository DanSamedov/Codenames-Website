FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /codenames
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /codenames/wait-for-it.sh

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=codenames.settings

EXPOSE 8000