FROM python:3.12-slim

RUN mkdir /work
RUN mkdir /work/app
RUN mkdir /work/data

WORKDIR /work

COPY ./requirements.txt /work
RUN pip install --no-cache-dir --timeout 1000 --retries 5 -r requirements.txt


COPY ./app/*.py /work/app
#COPY ./data/* /work/data

COPY ./base_logger.py /work

WORKDIR /work/app

CMD ["streamlit", "run", "app.py"]
