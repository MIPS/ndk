FROM ubuntu:trusty

RUN apt-get update

RUN apt-get install -y bison
RUN apt-get install -y build-essential
RUN apt-get install -y curl
RUN apt-get install -y dos2unix
RUN apt-get install -y flex
RUN apt-get install -y git
RUN apt-get install -y make
RUN apt-get install -y mingw-w64
RUN apt-get install -y pbzip2
RUN apt-get install -y python
RUN apt-get install -y texinfo
RUN apt-get install -y zip

RUN curl -o /usr/bin/repo \
    https://commondatastorage.googleapis.com/git-repo-downloads/repo
RUN chmod a+x /usr/bin/repo

CMD ["/bin/bash"]
