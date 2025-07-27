# Use a lightweight Python base image. Python 3.9 is a good stable choice.
FROM python:3.9-slim-buster

# Set the working directory inside the container.
WORKDIR /app

# Copy the entire project contents from your local machine to the /app directory in the container.
# The '.' refers to the current directory where the 'docker build' command is executed (your project root).
COPY . .

# Install Python dependencies.
# The '-r requirements.txt' flag tells pip to install packages listed in requirements.txt.
# '--no-cache-dir' is a best practice for Docker builds to reduce image size.
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that your FastAPI application will listen on inside the container.
# This makes the port visible to the outside world when the container is run.
EXPOSE 8000

# Define the command to run your application when the container starts.
# 'uvicorn' is the ASGI server that runs FastAPI.
# 'main:app' refers to the 'app' object in your 'main.py' file.
# '--host 0.0.0.0' makes the server listen on all available network interfaces,
# allowing it to be accessed from outside the container.
# '--port 8000' specifies the port it listens on.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]