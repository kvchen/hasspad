FROM balenalib/raspberry-pi-python:3.8-build

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hasspad

CMD ["hasspad", "/config.yml"]
