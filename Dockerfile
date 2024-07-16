# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Hong_Kong \
    CHROMEDRIVER_VERSION=126.0.6478.126

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Chrome
RUN apt-get update && apt-get install -y wget gnupg2 unzip \
    && wget -q <a href="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" class="underline" target="_blank">Click this URL</a> \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm ./google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN wget -q "<a href="https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"" class="underline" target="_blank">Click this URL</a> \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod 755 /usr/local/bin/chromedriver

# Add ChromeDriver to PATH
ENV PATH $PATH:/usr/local/bin/chromedriver

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "./bot.py"]