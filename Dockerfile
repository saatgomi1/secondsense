# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Run the application
CMD ["streamlit", "run", "secondsense.py", "--server.port=8501", "--server.enableCORS=false"]


# Expose the port the app runs on
EXPOSE 8501


