FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ="Europe/Rome"

RUN apt update 
RUN apt -y install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

ENV HOME="/root"
WORKDIR ${HOME}

RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install 3.9.10 3.9.18 nogil-3.9.10-1 3.10.13 3.11.8 3.12.2
RUN env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto --disable-gil' pyenv install 3.13.0b3
RUN pyenv global 3.12.2
RUN python -m pip install pyperformance
RUN $HOME/.pyenv/versions/3.9.10/bin/python -m pip install pyperformance requests flask aiohttp numpy==1.26.0 pandas
RUN $HOME/.pyenv/versions/3.9.18/bin/python -m pip install pyperformance requests flask aiohttp numpy==1.26.0 pandas
RUN $HOME/.pyenv/versions/nogil-3.9.10-1/bin/python -m pip install pyperformance requests flask aiohttp numpy<=1.26.0 pandas
RUN $HOME/.pyenv/versions/3.10.13/bin/python -m pip install pyperformance requests flask aiohttp numpy==1.26.0 pandas
RUN $HOME/.pyenv/versions/3.11.8/bin/python -m pip install pyperformance requests flask aiohttp numpy==1.26.0 pandas
RUN $HOME/.pyenv/versions/3.12.2/bin/python -m pip install requests flask aiohttp numpy==1.26.0 pandas
RUN $HOME/.pyenv/versions/3.13.0b3/bin/python -m pip install pyperformance requests flask aiohttp
RUN pip install telegram_send

ADD ./script.py /root
ADD ./fib.py /root
ADD ./telegram.conf /root
ADD ./versions.json /root
ADD ./new_benchmarks /root/new_benchmarks
RUN mkdir /root/pyperf_res
CMD ["python","-u","/root/script.py"]
