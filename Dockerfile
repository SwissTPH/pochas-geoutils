FROM ubuntu:20.04


LABEL maintainer="Behzad Valipour Sh. behzad.valipour@swisstph.ch"
LABEL version=0.0.1


RUN apt-get update \
    && apt-get install -y \
       git\
       nano \
       libopenblas-dev \
       liblapack-dev \
       libpq-dev \
       python-is-python3 \
       python3-pip \
       python3-dev \
       proj-bin \
    && rm -rf /var/lib/apt/lists/*

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y \
       software-properties-common \
    && apt-get update \
    && add-apt-repository ppa:ubuntugis/ppa \
    && apt-get update \
    && apt-get install -y \
               gdal-bin \
               libgdal-dev\
    && apt-get update

ENV export CPLUS_INCLUDE_PATH=/usr/include/gdal \
    export C_INCLUDE_PATH=/usr/include/gdal

# RUN pip3 install GDAL==3.2.1

COPY requirements.txt ./

pip3 install --no-cache-dir -r requirements.txt

CMD [ "/bin/bash" ]
#TODO: The requirements file should be prepared and the seperate repo in gitHUB should arrange for docker