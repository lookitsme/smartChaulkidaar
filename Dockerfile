FROM python:3.12.3

ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    graphviz \
    graphviz-dev \
    libgraphviz-dev \
    pkg-config \
    build-essential

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Adjust permissions for directories and files
RUN find . -type d -exec chmod 755 {} \; && \
    find . -type f -exec chmod 644 {} \;

# Make sure the entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Command to start the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
