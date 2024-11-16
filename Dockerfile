FROM python:3.9-alpine

# Install dependencies
RUN apk add --no-cache \
    build-base

# Create a directory for the application
WORKDIR /app

# Copy the wheels and install them
COPY dist/*.whl /app/
RUN pip install /app/*.whl

