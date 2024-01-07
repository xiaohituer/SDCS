"""
file: server.py
author: xiaohitu
create time: 2023/11/2
last modified: 2023/11/9
version: 5.0
description: server在作为一个http server的同时也是一个rpc server
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import rpyc
from rpyc import Service, ThreadedServer

port_http = 8080
host_http = "0.0.0.0"
port_rpc = 9991


# declaration: three port for http server is 9257,9258,9259
# three port for rpyc server is server:9991
# need to use dockerfile to make own network to make rpyc server work


cache_data = {
    "myname": "小嗨兔儿",
    "tasks": ["task 1", "task 2", "task 3"]
}


class HttpServertHandler(BaseHTTPRequestHandler):
    host_rpclist=["server1","server2","server3"]
    # 查找其他主机
    def find_other_hosts(self, key: str) -> str:
        for host in self.host_rpclist:
            conn = rpyc.connect(host, port_rpc)
            value = conn.root.exposed_Get(key)
            if len(value) > 0:
                return value
            conn.close()
        return ""

    def do_GET(self):
        '''
        获取get路径,处理get请求,
        :return:
        '''
        path = self.path
        key = ""
        # 获取get请求之后的路径
        if path.startswith("/"):
            parts = path.split("/")
            if len(parts) >= 2:
                key = parts[1]
        print(f"Accept get request, check key={key}")
        result = {}
        value = ""
        # 查找本机key
        if key in cache_data:
            value = str(cache_data[key])
        else:
            # 查找其他两个主机的
            value = str(self.find_other_hosts(key))
        if value:
            result[key] = value
            self.send_response(200)
            self.send_header('Content-type', "application/json")
            self.end_headers()
            response = json.dumps(result,separators=(',', ':'))
            self.wfile.write(response.encode("UTF-8"))
        else:
            self.send_response(404)
            self.send_header('Content-type', "text/plain")
            self.end_headers()
            response = ""
            self.wfile.write(response.encode("UTF-8"))

    def do_POST(self):
        '''
        收到更新请求是只更新本机cache
        :return:
        '''
        content_length = int(self.headers['Content-Length'])
        data_post = self.rfile.read(content_length).decode("UTF-8")
        try:
            request_data = json.loads(data_post)
            print(f"Accept post request, modify data={data_post}")
        except json.JSONDecodeError:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Invalid JSON data')
            return
        # 进行写入更新操作
        for k, v in request_data.items():
            cache_data[k] = v
        self.send_response(200)
        self.send_header('Content-type', "text/html")
        self.end_headers()
        response = "POST请求已处理"
        self.wfile.write(response.encode("UTF-8"))

    def delete_other_hosts(self, key: str) -> int:
        '''
         查询所有主机的key,并删除
        :param key:
        :return: 删除数量
        '''
        num = 0
        for host in self.host_rpclist:
            conn = rpyc.connect(host, port_rpc)
            value = conn.root.exposed_Delete(key)
            if value: num += 1
            conn.close()
        return num

    def do_DELETE(self):
        '''
        处理delete请求
        '''
        path = self.path
        key = ""
        # 获取get请求之后的路径
        if path.startswith("/"):
            parts = path.split("/")
            if len(parts) >= 2:
                key = parts[1]
        print(f"Accept delete request, delete data key is {key}")
        # 进行删除操作 删除操作需要全体删除
        number = 0
        if key in cache_data:
            number += 1
            del cache_data[key]
        number += self.delete_other_hosts(key)
        self.send_response(200)
        self.send_header('Content-type', "text/html")
        self.end_headers()
        response="1" if number>0 else "0"
        self.wfile.write(response.encode("UTF-8"))


class RpcRequestHandler(Service):

    # rpyc 部分
    def on_connect(self, conn):
        # 获取连接的客户端地址
        client_address = conn._channel.stream.sock.getpeername()

        # 获取当前线程信息
        current_thread = threading.current_thread()

        print(f"Accept rpc request from Client {client_address}")

    def exposed_Get(self, key: str) -> str:
        '''
        :param key:
        :return:
        '''
        if key in cache_data:
            print(f"Rpc get key={key},data={cache_data[key]}")
            return cache_data[key]
        return ""

    def exposed_Post(self, **kv: dict) -> bool:
        return True

    def exposed_Delete(self, key: str) -> bool:
        value = ""
        if key in cache_data:
            value = cache_data[key]
            del cache_data[key]
            print(f"Rpc delete key={key},data={value}")
        return value


# 启动HTTP服务器
def run_HttpServer():
    # 启动http 服务
    httpd = HTTPServer((host_http, port_http), HttpServertHandler)
    print(f'Starting HttpServer on address {(host_http, port_http)}...')
    httpd.serve_forever()


def run_RpcServer():
    # 启动rpyc 服务
    server_rpyc = ThreadedServer(RpcRequestHandler, port=port_rpc, auto_register=False)
    print(f'Starting RpcServer on address {port_rpc}...')
    server_rpyc.start()


if __name__ == "__main__":
    # 用多线程启动两个服务
    rpc_server = threading.Thread(target=run_RpcServer)
    http_server = threading.Thread(target=run_HttpServer)
    http_server.start()
    rpc_server.start()
