# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Copy only necessary files for running the application
FROM python:3.11-slim

WORKDIR /app
# Create a non-root user for security best practices
RUN useradd -m appuser
USER appuser

# Copy Python packages installed by pip --user from builder stage
# When pip install --user is run as root, packages go to /root/.local
COPY --from=builder /root/.local /home/appuser/.local

# Copy the entire project directory into the container's WORKDIR
COPY . .

# Set environment variable for Python to find user-installed packages
ENV PATH="/home/appuser/.local/bin:$PATH" 
# Add /app (the project root) to Python path
ENV PYTHONPATH="/app"
# Expose the port the application runs on
EXPOSE 8000

# Healthcheck to ensure container is healthy
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Command to run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}