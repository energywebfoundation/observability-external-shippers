FROM python

RUN mkdir /app
WORKDIR /app
ADD ./app /app/
RUN ls -la
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "/app/main.py"]
