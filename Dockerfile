FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto'

RUN apt-get update
RUN apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev wget git -y

RUN useradd -m python_user

WORKDIR /home/python_user
USER python_user

RUN git clone https://github.com/pyenv/pyenv.git .pyenv

ENV HOME  /home/python_user
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.12
RUN pyenv global 3.12
RUN pip install numpy pandas matplotlib
RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.9.10
RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.9.18
RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install nogil-3.9.10-1
RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.10
RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.11
