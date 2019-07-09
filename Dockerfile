FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y locales locales-all
RUN locale-gen ja_JP.UTF-8

RUN mkdir -p /opt/app

WORKDIR /opt/app

RUN pip install gunicorn psycopg2-binary

ADD requirements.txt /opt/app/
RUN pip install -r requirements.txt
ADD . /opt/app/
ENV DJANGO_SETTINGS_MODULE isucon.portal.docker_settings

CMD ["bash", "-xe", "entrypoint.sh"]

EXPOSE 5000
