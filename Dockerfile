FROM python:3.12-slim

RUN apt-get update && apt-get install -y git libpq-dev gcc

COPY requirements.txt /

RUN pip3 install --upgrade pip

RUN pip3 install -r /requirements.txt

COPY bibfilter/ /app/bibfilter

COPY gunicorn_config.py synchronize_pdf_content.py update_library.py setup_db.py app.py /app

WORKDIR /app

EXPOSE 80

CMD ["gunicorn","--config", "gunicorn_config.py", "app:app"]
