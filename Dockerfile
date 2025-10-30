# Use Python 3.12 (includes audioop)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install pip + setuptools + wheel first to ensure all dependencies build correctly
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Run the bot
CMD ["python", "KomiSec.py"]
