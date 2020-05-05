FROM python:3.6.10-slim-stretch

ARG ALLURE_RELEASE=2.13.3
ARG ALLURE_REPO=https://dl.bintray.com/qameta/maven/io/qameta/allure/allure-commandline
ARG UID=1000
ARG GID=1000

RUN mkdir -p /usr/share/man/man1 && \
    apt-get update -y && \
    apt-get install -y wget zip unzip default-jre && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN cd /opt && \
    wget --no-verbose -O /tmp/allure-$ALLURE_RELEASE.zip \
        $ALLURE_REPO/$ALLURE_RELEASE/allure-commandline-$ALLURE_RELEASE.zip && \
    unzip /tmp/allure-$ALLURE_RELEASE.zip -d . && \
    ln -s /opt/allure-$ALLURE_RELEASE/bin/allure /usr/bin/allure && \
    rm -rf /tmp/*

RUN groupadd --gid ${GID} allure_reporter && \
    useradd --uid ${UID} --gid allure_reporter --shell /bin/bash --create-home allure_reporter
WORKDIR /home/allure_reporter

COPY ./pyproject.toml ./poetry.lock /home/allure_reporter/
RUN pip install --no-cache poetry && \
    poetry config 'virtualenvs.create' false && \
    poetry install --no-dev

RUN mkdir /var/projectspace && chown -R allure_reporter /var/projectspace

USER allure_reporter
