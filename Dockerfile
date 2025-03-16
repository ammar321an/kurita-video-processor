FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenCV dependencies and tesseract
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download English language data for Tesseract
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata
RUN wget -O /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata

COPY . .

# Make sure video_processor.py is executable
RUN chmod +x video_processor.py

# Set environment variables for tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Set the PORT environment variable for Render
ENV PORT=10000

CMD gunicorn --bind 0.0.0.0:$PORT app:app