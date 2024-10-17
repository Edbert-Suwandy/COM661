FROM python:latest

WORKDIR /app

COPY requirement.txt .
RUN pip install -r requirement.txt

COPY ./app/** .

EXPOSE 5000

CMD ["python","-m", "flask", "--app", "app", "--debug","run" ,"--host","0.0.0.0"]