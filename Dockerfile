# Use official lightweight Python runtime as a parent image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY main.py .

# Run main.py when the container launches
CMD ["python", "main.py"]
