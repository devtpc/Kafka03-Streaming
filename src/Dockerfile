FROM python:3.6

ADD main.py /app/main.py
ADD requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install -r requirements.txt

ENTRYPOINT ["faust","-A","main","worker","-l","info"]
