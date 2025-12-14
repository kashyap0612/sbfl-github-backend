FROM python:3.11-slim

WORKDIR /repo

RUN pip install --no-cache-dir pytest coverage

COPY runner.py /runner.py

ENTRYPOINT ["python", "/runner.py"]
