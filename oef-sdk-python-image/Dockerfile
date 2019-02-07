FROM ubuntu:18.04

USER root
WORKDIR /root/

RUN apt-get update && \
    apt-get install -y g++ && \ 
    apt-get install -y make &&\
    apt-get install -y build-essential &&\
    apt-get install -y git &&\
    apt-get install -y cmake &&\
    apt-get install -y curl &&\
    apt-get install -y libssl-dev &&\
    apt-get install -y zlib1g-dev &&\
    apt-get install -y libbz2-dev &&\
    apt-get install -y libreadline-dev &&\
    apt-get install -y libsqlite3-dev &&\ 
    apt-get install -y libffi-dev

RUN apt-get install -y python3-pip python3-dev

RUN git clone git://github.com/yyuu/pyenv.git /root/.pyenv

ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="${PYENV_ROOT}/bin:${PATH}"

RUN echo 'eval "$(pyenv init -)"' >> /root/.bashrc

RUN pyenv install 3.5.6 -s
RUN pyenv install 3.6.8 -s
RUN pyenv install 3.7.2 -s
RUN pyenv global 3.5.6 3.6.8 3.7.2
 
RUN apt-get install -y tox
RUN pip3 install pipenv

RUN apt-get install -y \
     libprotobuf-dev libprotoc-dev \
     protobuf-compiler  python-protobuf

RUN mkdir /build
COPY . /build
WORKDIR /build
