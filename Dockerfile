# For faster build, I am using python:3.9-slim but python:3.9 would work as well
FROM python:3.9-slim

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./scraper.py"]
