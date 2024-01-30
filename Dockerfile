# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install protoc compiler
RUN apt-get update && apt-get install -y protobuf-compiler

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Grant execute permissions to the script
RUN chmod +x mqtt-sparkplugb.py

# Compile the sparkplug_b.proto file
RUN protoc --python_out=/usr/src/app proto/sparkplug_b.proto

# Move the generated Python file to the root directory
RUN mv proto/sparkplug_b_pb2.py ./

# Copy the requirements.txt file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run your application
CMD ["python", "./mqtt-sparkplugb.py"]
