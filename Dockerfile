# Use Python 3.12 to keep audioop
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "KomiSec.py"]
