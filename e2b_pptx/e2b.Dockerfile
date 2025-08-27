FROM e2bdev/code-interpreter:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /home/user

# Install required Python packages
RUN pip install --no-cache-dir \
    python-pptx \
    pandas \
    Pillow \
    environs

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1