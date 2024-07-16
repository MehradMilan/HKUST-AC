FROM python:3.9-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Hong_Kong

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - <a href="https://dl-ssl.google.com/linux/linux_signing_key.pub" class="underline" target="_blank">Click this URL</a> | apt-key add - \
    && echo "deb [arch=amd64] <a href="http://dl.google.com/linux/chrome/deb/" class="underline" target="_blank">Click this URL</a> stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm /etc/apt/sources.list.d/google-chrome.list \
    && rm -rf /var/lib/apt/lists/*

RUN CHROME_VERSION=$(google-chrome --version | cut -f 3 -d ' ' | cut -d '.' -f 1) \
    && CHROMEDRIVER_VERSION=$(wget -qO- "<a href="https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION"" class="underline" target="_blank">Click this URL</a> \
    && wget -q --continue -P /chromedriver "<a href="http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"" class="underline" target="_blank">Click this URL</a> \
    && unzip /chromedriver/chromedriver* -d /usr/local/bin/ \
    && rm /chromedriver/chromedriver_linux64.zip

ENV PATH $PATH:/usr/local/bin/chromedriver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./bot.py"]