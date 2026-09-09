FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install dependencies without storing pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app