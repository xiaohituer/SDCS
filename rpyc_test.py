"""
file: client1_rpyc
author: 
create time: 2023/11/2
last modified: 2023/11/2/19:56
version: 1.0
description: 
"""

import rpyc 

host= str(input("input host address\n"))
port=int(input("input port address\n"))
key=str(input("input key\n"))
conn= rpyc.connect(host,port=port)
# 这里root后面对应的方式是server中的expose_sum1 ,所以这里应该有两种写法,root.expose_sum1或者sum1都是正确的
result=conn.root.exposed_Get(key)
print(result)
conn.close()

