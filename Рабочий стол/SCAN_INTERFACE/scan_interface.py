#!flask/bin/python
from flask import Flask, jsonify

import threading #для реализации мультипоточности
import socket #для самого сканирования
import os #для полной остановки все потоков
import subprocess 
import sys 
import time 
import syslog
import json

#sudo python3 scanner_interface --objective 192.168.0.1 this is test


if("--objective" in sys.argv): 
    indexObjective=sys.argv.index("--objective") #индекс который занимает строка --objective в строке аргументов
    objective=sys.argv[indexObjective+1] #здесь записывается сама цель которую вводит пользователь после ввода --objective
else:
    print("Objective is not specified, see --help")
    exit()

if("--help" in sys.argv): #вызов помощи
    print("Usage: python3 scanner_interface.py --objective [objective]")
    print("Extra flags:")
    print("--port (-p) — specify port range for scan, by default 1-65535") #ввод промежутка портов
    exit()


if("--port" in sys.argv):
    indexPort=sys.argv.index("--port")
    port=sys.argv[indexPort+1] #ввод адреса порта 
    if("-" in port): #есть ли в значении которое ввел пользователь тире -
        port=port.split("-")
        begin_port=int(port[0]) #начальный порт для сканирования 0 а конечный 1
        end_port=int(port[1])
elif("-p" in sys.argv): #просто сокращение от --port
    indexPort=sys.argv.index("-p")
    port=sys.argv[indexPort+1]
    if("-" in port):
        port=port.split("-")
        begin_port=int(port[0])
        end_port=int(port[1])
else: #если ни -p ни --port не были введены, значения по умолчанию
    begin_port=1
    end_port=65535
    

#сканирование
start_time=time.time()

inputSocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

connectport = []
unconnectport =[]

#попытка соединения к порту
#если ошибка или порт закрыт то pass
def ScanPort(port):
    try:
        hostConnect = inputSocket.connect((objective,port))
        connectport.append(port)
        hostConnect.close()
    except Exception as e:
        unconnectport.append(port)

interval = begin_port
for interval in range(begin_port, end_port): #для каждого порта создается свой поток и выполняется паралельно
    try:
        t = threading.Thread(objective=ScanPort,kwargs={'port':interval})
        interval += 1
        t.start()
    except KeyboardInterrupt:
        os._exit(0)
    except Exception as e:
        ScanPort(interval)
        interval += 1

print(connectport)

#проверка завершились все потоки

threadslist=int(threading.active_count())
while threadslist>1:
    threadslist=int(threading.active_count())
    time.sleep(0.000001)

 
app = Flask(__name__)

jsonObjectsOpen = []
jsonObjectsClose = []

for step in connectport:
    opened = [
    {
        'port': step,
        'state': u'open', 
    }
    ]
    jsonObjectsOpen.append(opened)

for step1 in unconnectport:
    for step in connectport:
        if (step1 != step):
            close = [
        {
           'port': step1,
           'state': u'close', 
        }
        ]
        jsonObjectsClose.append(close)
            

@app.route('/', methods=['GET'])
def get_tasks():
    return jsonify({'opened': jsonObjectsOpen}, {'close': jsonObjectsClose})
 
if __name__ == '__main__':
    app.run(debug=True)