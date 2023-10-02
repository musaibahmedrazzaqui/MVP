# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the application's dependencies
RUN pip3 install -r requirements.txt

# Copy all the source code to the working directory
COPY . .

# Expose the port that the app will run on
EXPOSE 5000

# Define the command to start the app
CMD ["python", "app.py"]