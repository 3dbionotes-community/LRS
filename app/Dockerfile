FROM python:3.7
LABEL maintainer="jr.macias@cnb.csic.es"

# Setup as root ----------------------------------------------------
# Configure apt and install packages & Clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    sudo nano git curl bzip2 ca-certificates \
    python3-dev \
    2>&1 \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log


# Add default user
ARG USER_NAME
ARG USER_PASSWD
ARG USER_UID
ARG USER_GID
RUN groupadd --gid ${USER_GID} ${USER_NAME} \
    && useradd -m ${USER_NAME} -d /home/${USER_NAME} -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} \
    && echo "${USER_NAME}:${USER_PASSWD}"  | chpasswd \
    # Add sudo support
    && usermod -aG sudo ${USER_NAME} \
    && echo ${USER_NAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USER_NAME} \
    && chmod 0440 /etc/sudoers.d/${USER_NAME}


# Setup as user ----------------------------------------------------
USER ${USER_NAME}
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED 1

# Setup Django App
RUN mkdir -p /home/${USER_NAME}/lrs/app
COPY . /home/${USER_NAME}/lrs/app
WORKDIR /home/${USER_NAME}/lrs/app
RUN pip install -r requirements.txt