FROM python:3.11-slim

# Install Java for WEKA
RUN apt-get update && \
    apt-get install -y default-jdk && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME (optional, some Java tools need it)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 10000

# Start Flask via gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
