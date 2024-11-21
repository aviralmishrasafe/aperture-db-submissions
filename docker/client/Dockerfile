FROM ubuntu:22.04

RUN apt update && apt install -y python3-pip
RUN pip install --upgrade pip
RUN pip install aperturedb
ADD setup.sh /
RUN mkdir /app
COPY app /app
#CMD tail -f /dev/null
CMD bash /setup.sh
