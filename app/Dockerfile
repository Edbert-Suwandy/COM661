# syntax=docker.io/docker/dockerfile:1.7-labs
FROM python:latest
WORKDIR /app

COPY requirement.txt .
RUN pip install -r requirement.txt
COPY --exclude=./db/** --exclude=./datastore/** --exclude=./venv/** . .
EXPOSE 5000

CMD ["python","-m", "flask","--app","app/app.py", "--debug","run" ,"--host","0.0.0.0"]
