# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
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

 # EPEL: Extra Packages for Enterprise Linux 9
 # `epel-release` is not recent/complete enough, as some packages below are missing
 RUN dnf config-manager --set-enabled crb && \
     dnf install -y \
         https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm

# Install needed and useful tools:
#  - python and friends
#  - basic system tools (procps-ng, htop, less, git, glibc, wget, curl)
#  - process/file inspection tools (strace, lsof, file)
#  - performance monitoring tools (iotop, iftop)
#  - networking tools (tcpdump, bind-utils)
# The installation of "Development Tools" should not be required. Be aware of its
# size ~1.1 Gb
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
        xmlsec1-devel && \
        # procps-ng htop less \
        # strace lsof file \
        # iotop iftop \
        # tcpdump bind-utils && \
    dnf clean all

# Symlink Python
# RUN ln -sfn /usr/bin/python3 /usr/bin/python
# `python3-packaging` is installed by `yum` and it causes issues with `pip` installations
# RUN yum remove python3-packaging -y
RUN pip install --upgrade pip pipenv wheel



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
#RUN dnf upgrade -y && dnf clean all

COPY site ./site
COPY Pipfile Pipfile.lock ./
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations/ ${INVENIO_INSTANCE_PATH}/translations/
COPY ./ .

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    /opt/invenio/src/.venv/bin/invenio collect --verbose  && \
    /opt/invenio/src/.venv/bin/invenio webpack buildall

    # Make directory owned by Invenio user
RUN chown -R invenio test_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
