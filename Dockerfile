FROM ubuntu:22.04
ENTRYPOINT ["tail", "-f", "/dev/null"]
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt install kmod build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev wget -y

ENV HOME="/root"
WORKDIR ${HOME}

RUN apt-get install -y git
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

RUN pyenv install 3.12
#RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.12
RUN pyenv global 3.12
RUN pip install pyperformance numpy pandas matplotlib telegram_send

ADD . /home/python_user/NoGILExperiments

#RUN python -m pyperf system tune
#CMD ["python","/home/python_user/NoGILExperiments/script.py"]
