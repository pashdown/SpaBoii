ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache gcc musl-dev

WORKDIR /app

COPY app/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ .
COPY integration/ /integration/

CMD ["python3", "main.py"]
