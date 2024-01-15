FROM python

WORKDIR /usr/app/bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]