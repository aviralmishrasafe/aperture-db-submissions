# FROM aperturedata/aperturedb-standalone
# FROM --platform=linux/amd64 aperturedata/aperturedb-standalone
FROM aperturedata/aperturedb-community
RUN apt update
RUN apt install -y  python3-pip
RUN pip install aperturedb

ADD add_users.sh /
ADD start.sh /
ADD add_user.py /

CMD ["/start.sh"]
#ENTRYPOINT /start.sh
