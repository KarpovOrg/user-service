FROM ubuntu:latest
LABEL authors="Stefan"

ENTRYPOINT ["top", "-b"]