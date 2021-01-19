FROM arm32v6/python:3

RUN mkdir /hasspad

COPY /hasspad /hasspad
COPY pyproject.toml /hasspad

WORKDIR /hasspad
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT ["python3", "/hasspad/main.py"]
