FROM python:3.11.6

ARG CONDA_PATH=/miniconda

COPY . /wofost
WORKDIR /wofost

# Miniconda https://docs.anaconda.com/miniconda/
RUN mkdir -p "${CONDA_PATH}"
RUN arch=$(uname -m) && wget "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${arch}.sh" -O "${CONDA_PATH}/miniconda.sh"
RUN bash "${CONDA_PATH}/miniconda.sh" -b -u -p "${CONDA_PATH}"
RUN rm -f "${CONDA_PATH}/miniconda.sh"

# Users can run some apt commands and access conda
RUN addgroup wofost-users

# Make conda command available to all
RUN chown -R root:wofost-users "${CONDA_PATH}"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
    # Generate SSH key for usage with git
    openssh-server && \
    apt-get -y upgrade && \
    apt-get -y clean && \
    apt-get -y autoremove --purge && \
    rm -rf /var/lib/apt/lists/* /tmp/*


RUN ${CONDA_PATH}/bin/conda env create -f wofost-env.yml

# Users
ARG USERS="dw356 ik354 mh1176 trfb201 jm622 mcm216"
ARG USER_IDS="502 505 503 507 504 506"

# Make conda command available to all
ARG PATH_DOLLAR='$PATH' # do not interpolate $PATH, this is meant to update path in .bashrc
ARG COMMAND_EXPORT_PATH_BASHRC="export PATH=\"${CONDA_PATH}/bin:${PATH_DOLLAR}\""
# $COMMAND_EXPORT_PATH_BASHRC contains: export PATH="<conda_path>/bin:$PATH"
RUN echo "${COMMAND_EXPORT_PATH_BASHRC}" | tee -a "/etc/bash.bashrc"


ARG DEFAULT_PASSWORD="orchid"

# Initialize users
RUN bash -c ' \
        USERS_ARRAY=($USERS); \
        USER_IDS_ARRAY=($USER_IDS); \
        for i in "${!USERS_ARRAY[@]}"; do \
            user="${USERS_ARRAY[i]}" && \
            user_id="${USER_IDS_ARRAY[i]}" && \
            adduser --disabled-password --comment "" --uid "${user_id}" --shell /bin/bash "${user}" && \
            echo "${user}:${DEFAULT_PASSWORD}" | chpasswd && \
            usermod --append --groups wofost-users "${user}" ; \
        done \
    '

# Initalize conda for everyone
RUN ${CONDA_PATH}/bin/conda init

# Let users install packages, update package list, search
RUN mkdir -p /etc/sudoers.d
RUN bash -c 'echo "User_Alias MYUSERS = ${USERS// /,}" | tee /etc/sudoers.d/group-wofost-users'
RUN echo "Cmnd_Alias INSTALL = /usr/bin/apt-get install *, /usr/bin/apt install *" >> /etc/sudoers.d/group-wofost-users
RUN echo "Cmnd_Alias UPDATE = /usr/bin/apt-get update, /usr/bin/apt update" >> /etc/sudoers.d/group-wofost-users
RUN echo "Cmnd_Alias SEARCH = /usr/bin/apt-get search, /usr/bin/apt search" >> /etc/sudoers.d/group-wofost-users
RUN echo "MYUSERS ALL = INSTALL, UPDATE, SEARCH" >> /etc/sudoers.d/group-wofost-users

EXPOSE 22

ENTRYPOINT tail -f /dev/null