FROM balenalib/raspberry-pi-python:3.8-build

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY ./hasspad /hasspad

WORKDIR /hasspad
ENTRYPOINT ["python3", "/hasspad/main.py"]
