FROM ubuntu:20.04

RUN apt-get update && apt-get install -y python3 python3-pip curl

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rpyc

# http port
EXPOSE 8080
#rpc port
EXPOSE 9991

COPY ./server.py /tmp/
#rpyc test
COPY ./rpyc_test.py /tmp/

#shell test
COPY ./sdcs-test.sh /tmp/

CMD ["python3", "/tmp/server.py","8080","--bind","0.0.0.0","9991","--bind","0.0.0.0"]
