FROM python:3.7.3
COPY ./app /code/app
COPY ./node_modules/govuk-frontend/assets /code/app/assets
COPY ./node_modules/govuk-frontend/all.js /code/app/static/js/govuk.js
COPY requirements.txt /code/
COPY run.py /code/
COPY migrations /code/migrations
COPY config.py /code/config.py
COPY reporting /code/reporting
COPY modules /code/modules
WORKDIR /code
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT flask run --host 0.0.0.0