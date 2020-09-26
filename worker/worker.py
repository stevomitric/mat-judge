import socket, time, os, json, sys

from threading import Thread

import urllib.request
import judge as jg

from mod.default import *

# Change path to scripts
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

class Main:
    def __init__(self):
        self.IS_ALIVE = True
        self.CONNECTED = False

        jg.init_sandbox()

    def connect(self, ignore_failed = False):
        ''' Connects to the worker controller '''

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            log.write("Attempting to connect...")

            self.socket.connect( (SERVER['ip'], SERVER['port']) )
            self.socket.settimeout(1)
            
            connect = socket_protocol_create_request(['connect', 'c'])
            self.socket.send(connect)
            self.CONNECTED = True

            log.write('Connected to main server')
        except Exception as e:
            if not ignore_failed:
                raise RuntimeError('Failed to connect: '+ str(e) )
            log.write('Failed to connect: ' + str(e))

    def handle_wait(self, tm, msg = 'Keyboard Exception caught'):
        try:
            time.sleep(tm)
        except KeyboardInterrupt:
            self.IS_ALIVE = False
            log.write(msg)

    def main_loop(self):
        ''' Watch the network for incoming requests '''

        while self.IS_ALIVE:
            # Avoid fast resourse drain with inf loop
            self.handle_wait(0.05, 'Bye')

            # While not connected, try to connect
            while self.IS_ALIVE and not self.CONNECTED:
                self.handle_wait(1,'Bye')
                self.connect(ignore_failed=True)

            data = socket_protocol_recieve(self.socket, close_on_timeout=False)
            if data == SOCKET_RECV_EMPTY or data == SOCKET_RECV_FAILED:
                self.socket.close()
                self.CONNECTED = False
                continue

            elif data == SOCKET_RECV_TIMEOUT:
                continue
		
	    # Not in thread in order to maintain 'ordered responses'
            self.parse_request(data)

    def parse_request(self, data):
        message = json.loads(data[0])
        if message['request']!='ping':
            print ("recieved:", message)

        if message['request'] == 'submit':
            # message['data'] follows protocol clause worker#1.1
            sub = message['data']
            res = jg.submit(sub)

        if message['request'] == 'status':
            # message['data'] follows protocol clause worker#1.3
            stat = message['data']
            res = jg.get_state(stat)
            self.send_data(json.dumps(res))

        if message['request'] == 'workload':
            self.send_data(json.dumps({'workload': jg.WORKLOAD}))

        if message['request'] == 'cpu-ussage':
            # return cpu ussage
            pass

        if message['request'] == 'is-working':
            # check wheater working is running a submission
            pass


    def send_data(self, data):
        data = socket_protocol_create_request([data])
        try:
            self.socket.send(data)
        except:
            self.CONNECTED = False
            return -1
        return 0

if __name__ == "__main__":
    #if os.geteuid():
    #    print ("You must run this script as root")
    #    sys.exit(0)

    obj = Main()

    Thread( target = obj.main_loop).start()

    while 1:
        try:
            input()
        except:
            os.kill(os.getpid(), 9)
