FROM python:3.12-slim

RUN useradd -m -u 1000 scripter

RUN mkdir /app

USER scripter

WORKDIR /app

COPY *.py ./
COPY .env ./
COPY requirements.txt ./

RUN pip install -r requirements.txt

EXPOSE ${PORT}

CMD ["python3", "main.py"]
