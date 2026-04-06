ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache gcc musl-dev

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ .
COPY integration/ /integration/

CMD ["/usr/bin/with-contenv", "python3", "-u", "main.py"]
