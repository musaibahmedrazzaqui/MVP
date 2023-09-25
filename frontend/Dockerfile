# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install app dependencies
RUN npm install

# Copy all the source code to the working directory
COPY . .

# Expose the port that the app will run on
EXPOSE 3000

# Define the command to start the app
CMD ["npm", "start"]