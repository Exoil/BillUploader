FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for bills
RUN mkdir -p /app/bills
RUN mkdir -p /app/logs

# Expose the port the app runs on
EXPOSE 8050

# Command to run the application
CMD ["python", "main.py"] 