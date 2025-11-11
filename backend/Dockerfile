FROM python:3.10-slim

# Working directory for application code
WORKDIR /usr/src/app

# Environment setup
ENV PYTHONPATH=/usr/src/app
ENV DATABASE_PATH=/data/names.db

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Create a directory for database storage
RUN mkdir -p /data

EXPOSE 5000

# Run Gunicorn server
CMD ["gunicorn", "-w", "4", "--chdir", "/usr/src/app", "--bind", "0.0.0.0:5000", "app:app"]
