# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, uv, Node.js, NPM and some few standard libraries
# Invenio usually needs.
#
# Note: It is important to keep the commands in this file in sync with your
# bootstrap script located in ./scripts/bootstrap.

ARG LINUX_VERSION=10.0
ARG BUILDPLATFORM=linux/amd64
FROM --platform=$BUILDPLATFORM almalinux:${LINUX_VERSION}

RUN dnf upgrade --refresh -y && \
    dnf install -y \
        dnf-plugins-core \
        git \
        glibc-common \
        glibc-locale-source \
        glibc-langpack-en \
        gcc && \
    dnf clean all

RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN dnf config-manager --set-enabled crb && \
     dnf install -y \
         https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm && \
    dnf clean all


# Install needed and useful tools:
#  - python and friends
#  - basic system tools (procps-ng, htop, less, git, glibc, wget, curl)
#  - process/file inspection tools (strace, lsof, file)
#  - performance monitoring tools (iotop, iftop)
#  - networking tools (tcpdump, bind-utils)
RUN dnf install -y \
        pip \
        python3-devel \
        cairo-devel \
        dejavu-sans-fonts \
        libffi-devel \
        libpq-devel \
        libxml2-devel \
        libxslt-devel \
        ImageMagick \
        openssl-devel \
        bzip2-devel \
        xz-devel \
        sqlite-devel \
        which \
        nodejs \
        xmlsec1-devel \
        libatomic && \
    dnf clean all

# Symlink Python
RUN pip install --upgrade pip uv wheel --no-cache-dir


# Create working directory
ENV WORKING_DIR=/opt/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance

# Create files mountpoints
RUN mkdir -p ${WORKING_DIR}/src && \
    mkdir -p ${INVENIO_INSTANCE_PATH} && \
    mkdir \
        ${INVENIO_INSTANCE_PATH}/data \
        ${INVENIO_INSTANCE_PATH}/archive \
        ${INVENIO_INSTANCE_PATH}/static

# Invenio file will be in <WORKING_DIR>/src
WORKDIR ${WORKING_DIR}/src

# Set folder permissions
ENV INVENIO_USER_ID=1000
RUN chgrp -R 0 ${WORKING_DIR} && \
    chmod -R g=u ${WORKING_DIR} && \
    useradd invenio --uid ${INVENIO_USER_ID} --gid 0 && \
    chown -R invenio:root ${WORKING_DIR}

COPY site ./site
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
ENV VIRTUAL_ENV_PATH=${WORKING_DIR}/src/.venv
ENV PATH="$VIRTUAL_ENV_PATH/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations/ ${INVENIO_INSTANCE_PATH}/translations/
COPY ./ .

RUN curl -fsSL https://get.pnpm.io/install.sh | ENV="$HOME/.bashrc" SHELL="$(which bash)" bash -

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose  && \
    PATH=$PATH:/root/.local/share/pnpm/bin/ invenio webpack buildall && \
    /root/.local/share/pnpm/bin/pnpm cache delete

RUN chown -R invenio test_data/ ${INVENIO_INSTANCE_PATH}/app_data/
