FROM python:3.10-slim

WORKDIR /app

# Install only essential system dependencies needed for native python builds
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the standard port Cloud Run listens on
EXPOSE 8080

# Configure Streamlit to run smoothly in a containerized serverless environment
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]