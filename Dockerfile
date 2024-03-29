FROM python:3.8-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

CMD ["python", "-u", "main.py"]