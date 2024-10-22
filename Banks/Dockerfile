# Stage 1: Build dependencies
FROM python:3.9 AS builder

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --user -r requirements.txt

# Stage 2: Final image
FROM python:3.9-slim

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the library path for poppler
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# After installing runtime dependencies
RUN which pdftoppm && pdftoppm -v

# Copy application code
COPY UOB ./UOB
COPY Citi ./Citi
COPY DBS ./DBS
COPY main.py .

# Run the main script
CMD ["python", "main.py"]
