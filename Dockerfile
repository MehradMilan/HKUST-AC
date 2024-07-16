FROM python:3.8.10

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Hong_Kong

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV CHROMEDRIVER_VERSION=114.0.5735.90

RUN apt-get update && apt-get install -y wget && apt-get install -y zip
RUN wget -q https://www.slimjet.com/chrome/download-chrome.php?file=files%2F104.0.5112.102%2Fgoogle-chrome-stable_current_amd64.deb
RUN dpkg -i download-chrome.php?file=files%2F104.0.5112.102%2Fgoogle-chrome-stable_current_amd64.deb || apt-get -f install -y
RUN rm -f download-chrome.php?file=files%2F104.0.5112.102%2Fgoogle-chrome-stable_current_amd64.deb

RUN wget https://chromedriver.storage.googleapis.com/104.0.5112.79/chromedriver_linux64.zip \
  && unzip chromedriver_linux64.zip && rm -dfr chromedriver_linux64.zip \
  && mv chromedriver /usr/bin/chromedriver \
  && rm -rf LICENSE.chromedriver \
  && chmod 777 /usr/bin/chromedriver

RUN echo "Chrome: " && google-chrome --version

ENV PATH $PATH:/usr/bin/chromedriver
ENV DISPLAY=localhost:11.1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./bot.py"]