FROM python:3.7
LABEL maintainer="jr.macias@cnb.csic.es"

# Setup as root ----------------------------------------------------
# Configure apt and install packages & Clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    openssh-server supervisor tmux \
    sudo nano git curl bzip2 ca-certificates \
    python3-dev \
    gcc-8 g++-8 cmake openjdk-11-jdk \
    libxft-dev libssl-dev libxext-dev libxml2-dev \
    libreadline-dev libquadmath0 libxslt1-dev libopenmpi-dev openmpi-bin  libxss-dev libgsl0-dev libx11-dev \
    gfortran libfreetype6-dev scons libfftw3-dev libopencv-dev \
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

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN mkdir /var/run/sshd


# Setup as user ----------------------------------------------------
USER ${USER_NAME}
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
RUN mkdir -p /home/${USER_NAME}/lrs/tools
RUN mkdir -p /home/${USER_NAME}/lrs/data
WORKDIR /home/${USER_NAME}/lrs/tools

# Install Scipion-2
RUN curl -o scipion_v2.0_2019-04-23_linux64_Ubuntu.tgz http://scipion.i2pc.es/startdownload/?bundleId=3
RUN tar xfv scipion_v2.0_2019-04-23_linux64_Ubuntu.tgz
WORKDIR /home/${USER_NAME}/lrs/tools/scipion/pyworkflow/templates
RUN sed -i "s@SCIPION_NOTIFY = False@SCIPION_NOTIFY = True@g" scipion.template 
RUN sed -e "s@/usr/lib64/mpi/gcc/openmpi/lib@/usr/lib/x86_64-linux-gnu/openmpi/lib@" scipion.template
RUN sed -e "s@/usr/lib64/mpi/gcc/openmpi/include@/usr/lib/x86_64-linux-gnu/openmpi/include@" scipion.template
WORKDIR /home/${USER_NAME}/lrs/tools/scipion
RUN ./scipion config
WORKDIR /home/${USER_NAME}/lrs/tools/scipion
RUN ./scipion install -j 5

# Setup supervisor
USER root
COPY init.conf /etc/supervisor/conf.d/init.conf
CMD ["supervisord", "-n"]