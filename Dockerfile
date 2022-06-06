FROM python

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install flask

COPY app.py .

CMD [ "python3", "app.py"]
