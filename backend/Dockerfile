# Use an official Python runtime as a parent image 
FROM python:3.9-slim-buster

# Set the working directory in the container 
WORKDIR /app

# Update system packages
RUN apt-get update

# Install system dependencies
RUN apt-get install -y \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libffi-dev \
    libjpeg-dev \
    libgif-dev \
    libpixman-1-dev \
    gcc

RUN apt-get install -y sox ffmpeg libcairo2 libcairo2-dev

# Upgrade pip
RUN pip install --upgrade pip

# Install WeasyPrint and pycairo
RUN pip3 install weasyprint
RUN pip3 install pycairo

# Copy the requirements file into the container 
COPY requirements.txt .

# Install the application's dependencies 
RUN pip3 install -r requirements.txt

# Copy all the source code to the working directory 
COPY . .

# Expose the port that the app will run on 
EXPOSE 5001

# Define the command to start the app 
CMD ["python", "app.py"]
