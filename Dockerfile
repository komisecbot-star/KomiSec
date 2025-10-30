# --- Dockerfile ---
# Force Python 3.12 to avoid missing audioop on Python 3.13+
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first for better caching
COPY requirements.txt .

# Install all required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot code
COPY . .

# Run the bot when container starts
CMD ["python", "KomiSec.py"]
