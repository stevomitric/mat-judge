import socket, json, os, time, sys

from threading import Thread

# pylint: disable-all
from mod.default import *
from testcase_manager import Testcases
from token_manager import Token
from limits import Limits
from db.db_manager import DB

class Worker:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.conn.settimeout(1)
        
        self.COMMUNICATE = False

        log.write('Worker connected')

    def recieve_message(self, timeout = 1):
        # check if self.conn object is still a socket
        try:
            self.conn.settimeout(timeout)
            data = socket_protocol_recieve(self.conn)
        except:
            return SOCKET_RECV_FAILED
        if data == SOCKET_RECV_FAILED or data == SOCKET_RECV_EMPTY or data == SOCKET_RECV_TIMEOUT:
            log.write("Failed to recieve message from controller (code: " + str(data) + ")")
        return data

    def send_message(self, msg):
        message = socket_protocol_create_request(msg)
        try:
            self.conn.send(message)
        except Exception as e:
            log.write("Failed to send message to controller: " + str(e))
            return -1
        return 0

    def communicate(self, msg, recieve = False):
        ''' Communicates with the worker, thread-save way '''
        while self.COMMUNICATE:
            time.sleep(0.01)
        self.COMMUNICATE = True
        try:
            print('sent:',msg)
            res = self.send_message(msg)
            if (recieve):
                print ('recieving...')
                res = self.recieve_message()
                print('recieved:',res)
        except:
            res = -1
        self.COMMUNICATE = False
        return res



class Main:
    def __init__(self):
        self.IS_ALIVE = True
        self.socket = None

        self.db = DB() 
        self.tc_manager = Testcases(self.db)
        self.token_manager = Token(self.db)
        self.limits = Limits(self.db.getConf()[3], self.db.getConf()[4])

        self.queue = []
        self.workers = []

        self.allowed_languages = ['c++11', 'c++14', 'c++17']

    def loadSubID(self):
        id = self.db.getConf()[0]
        self.db.saveConf('sub_id', id+1)
        return id

    def startLoop(self):
        Thread(target = self.server_loop_thread).start()
        Thread(target = self.queue_workers).start()

    def shutdown(self):
        self.IS_ALIVE = False
        self.socket.close()

        os.kill(os.getpid(), 9)

    def create_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind( (SERVER['ip'], SERVER['port']) )
        except Exception as e:
            log.write("Failed to start socket: " + str(e), 'warn')
            self.shutdown()

        self.socket.settimeout(1)
        self.socket.listen(10)
        return 0

    def server_loop_thread(self):
        if self.create_server():
            return -1

        log.write("Socket started, listening for requests ...")
        while (self.IS_ALIVE):
            time.sleep(0.5)

            # Ping all workers every 5 seconds
            if (int(time.time()) % 10 <= 1 ):
                self.ping_workers()

            try:
                conn, addr = self.socket.accept()
                conn.settimeout(1)
                data = socket_protocol_recieve(conn)

                if data == SOCKET_RECV_TIMEOUT or data == SOCKET_RECV_EMPTY or data == SOCKET_RECV_FAILED:
                    conn.close()
                    log.write("Invalid connect packet, connection terminated")
                    continue
            except:
                continue

            log.write("Recieving worker from {}".format(addr))

            worker = Worker(conn, addr )
            self.workers.append(worker)

    def queue_workers(self):
        ''' Processing worker queue '''
        while self.IS_ALIVE:
            time.sleep(0.5)
            queue = self.queue[:]
            self.queue = []
            overhead = []

            for task in queue:
                # Slow down network overhead
                time.sleep(0.1)

                # Determine worker with lowest workload
                best, worker  = 999, None
                for wrk in self.workers[:]:
                    res = wrk.communicate([json.dumps({
                        'request': 'workload',
                    })], True)

                    if res in [SOCKET_RECV_EMPTY, SOCKET_RECV_FAILED, SOCKET_RECV_TIMEOUT]:
                        log.write("Bad worker.")
                        self.remove_worker(wrk)
                        continue

                    try:
                        res = json.loads(res[0])['workload']
                    except:
                        log.write("Bad worker response.")
                        continue

                    if (res < best):
                        best = res
                        worker = wrk
                        
                # Check if any worker responded
                if not worker:
                    overhead.append(task)
                    continue

                # Limit workload to 3
                if best > 3:
                    overhead.append(task)
                    continue

                # Send queue request to worker
                if task['request'] == 'submit':
                    print('sent:', task)
                    worker.communicate([json.dumps(task)])

            # Requeue (at front) tasks that failed to execute
            # + self.queue -  some might have queued meanwhile
            self.queue = overhead + self.queue

    def get_status(self, req):
        for worker in self.workers[:]:
            response = worker.communicate([json.dumps(req)], True)

            if response in [SOCKET_RECV_EMPTY, SOCKET_RECV_FAILED, SOCKET_RECV_TIMEOUT]:
                log.write("Bad worker.")
                self.remove_worker(worker)
                continue
            response = json.loads(response[0])
            if 'error' in response and 'running' not in response:
                continue
            response.update({'success': True})
            return response
        return {'success': False, 'error': 'Invalid submission ID'}

    def valid_submission(self, sub):
        ''' Validate the submit request, return a tuple (status, formated) '''

        # Required fields
        req = ['code', 'language']
        for field in req:
            if field not in sub:
                return (0, 'Field "{}" is required'.format(field))
        
        # Check unknown keys
        allowed_keys = ['submission_id', 'language', 'code', 'time_limit', 'memory_limit', 'testcases', 'testcases_id', 'grader']
        for key in sub:
            if key not in allowed_keys:
                return (0, "Unrecognised field '{}'".format(key) )

        # Check for passive-submissions
        passive_submissions = self.db.getConf()[2]
        if passive_submissions:
            only_keys = ['code', 'language', 'testcases_id', 'submission_id']
            for key in sub:
                if key not in only_keys:
                    return (0, "Passive submission doesn't allow: '{}'".format(key) )
            if 'testcases_id' not in sub:
                return (0, "Passive submission requires testcases_id")


        # Replace common languages to accepted format
        lang_repl = {'c++':'c++11'}
        for lang in lang_repl:
            if sub['language'] == lang:
                sub['language'] = lang_repl[lang]

        # Check for allowed languages
        languages = self.allowed_languages
        if sub['language'] not in languages:
            return (0, 'Language {} is not supported'.format( sub['language'] ))

        # Apply default filters
        default = {
            'time_limit': 1000,
            'memory_limit': 256,
            'testcases': [],
            'testcases_id': -1,
            'grader': '',
        }
        for key in default:
            if key not in sub or not sub[key]:
                sub[key] = default[key]

        # Format to integers
        try:
            sub['time_limit'] = int(sub['time_limit'])
            sub['memory_limit'] = int(sub['memory_limit'])
        except:
            return (0, 'Invalid time/memory resourse value')

        # Format to list of tuples or load tc form file
        sub['testcases'] = self.tc_manager.validTestcases(sub['testcases'])
        if not sub['testcases']:
            sub['testcases'] = self.tc_manager.loadTestcases( sub['testcases_id'] )

            if 'error' in sub['testcases']:
                return (0, 'Testcases should be a list of tuples, or provide a valid testcases ID ')
            else:
                sub['testcases'] = sub['testcases']['testcases']

        # Limit resources
        if sub['time_limit'] > 15*1000:
            return (0, "Time limit can't be grather then 15000ms")
        elif sub['time_limit'] < 100:
            return (0, "Time limit can't be lower then 100ms")
        elif sub['memory_limit'] > 256:
            return (0, "Memory limit can't be grather then 256mb")
        elif sub['memory_limit'] < 4:
            return (0, "Memory limit can't be lower then 4mb")

        return (1, sub)

    def valid_status(self, stat):
        ''' Validate the status request, returns a tuple (status, formated) '''
        
        # Required fields
        req = ['submission_id']
        for field in req:
            if field not in stat:
                return (0, 'Field "{}" is required'.format(field))

        # Check unknown keys
        allowed_keys = ['submission_id', 'output']
        for key in stat:
            if key not in allowed_keys:
                return (0, 'Unrecognised field "{}"'.format(key) )
        
        # Check if output is in valid format
        if 'output' in stat:
            try:
                stat['output'] = bool(eval(stat['output']))
            except:
                return (0, 'Output field has unknown value "{}"'.format(stat['output']))

        # Fix output format if it is not included
        if 'output' not in stat:
            stat['output'] = False
        
        return (1, stat)


    def add_queue(self, task):
        if (task['request'] == 'submit'):
            valid = self.valid_submission( task['data'] )
            if valid[0]:
                if (len(self.queue) > 20):
                    return {'success': False, 'error': "Queue is full. Try again in few moments"}

                task['data'] = valid[1]
                task['data']['submission_id'] = self.loadSubID()
                self.queue.append(task)
                return {'success': True, 'submission_id': task['data']['submission_id']}
            else:
                return {'success': False, 'error': valid[1]}
        
        if (task['request'] == 'status'):
            # Check if status is in valid format
            valid = self.valid_status(task['data'])
            if (not valid[0]):
                return {'success': False, 'error': valid[1] }
            task['data'] = valid[1]

            return self.get_status(task)

        if (task['request'] == 'testcases'):
            if 'testcases' not in task['data']:
                return {'success': False, 'error': "testcases field is required"}
            else:
                res = self.tc_manager.saveTestcases(task['data']['testcases'])
            if 'error' in res:
                res['success'] = False
            else:
                res['success'] = True
            return res

        if (task['request'] == 'create-token'):
            req = self.token_manager.validateRequest(task['data'])
            if not req[0]:
                return {'success': False, 'error': req[1] }
            else:
                token = self.token_manager.createToken(req[1]['owner'], req[1]['expiration'], req[1]['access_level'] )
                return {'success': True, 'token': token}

        if (task['request'] == 'info-token'):
            req = self.token_manager.tokenInformation(task['data']['token'])
            if not req[0]:
                return {'success': False, 'error': req[1] }
            else:
                return {'success': True, 'token': task['data']['token'], 'owner': req[1]['owner'], 'access_level':req[1]['access_level'], 'expiration':req[1]['expiration']-time.time() }

        if (task['request'] == 'delete-token'):
            req = self.token_manager.deleteToken(task['data']['token'], task['data']['owner'])
            if not req[0]:
                return {'success': False, 'error': req[1] }
            else:
                return {'success': True, 'message': req[1]}

        if (task['request'] == 'settings'):
            try:
                changed = []
                if 'token_access' in task['data']:
                    self.db.saveConf('token_access', task['data']['token_access'])
                    changed.append('token_access')
                if 'passive_submissions' in task['data']:
                    self.db.saveConf('passive_submissions', task['data']['passive_submissions'])
                    changed.append('passive_submissions')
                if 'ip_status_timeout' in task['data']:
                    self.db.saveConf('ip_status_timeout', task['data']['ip_status_timeout'])
                    changed.append('ip_status_timeout')
                if 'ip_submit_timeout' in task['data']:
                    self.db.saveConf('ip_submit_timeout', task['data']['ip_submit_timeout'])
                    changed.append('ip_submit_timeout')
                self.limits.setLimits(self.db.getConf()[3], self.db.getConf()[4])
            except Exception as e:
                return {'success': False, 'error': str(e)}
            if not changed:
                return {'success': False, 'error': 'Nothing has been changed. No valid argument provided.'}
            return {'success': True, 'message': 'Changed '+', '.join(changed)}

        else:
            return {'success':False,'error': 'Unknown request'}

    def ping_workers(self):
        for worker in self.workers[:]:
            res = worker.communicate([json.dumps({
                'request': 'ping',
            })])
            if res:
                self.remove_worker(worker)

    def remove_worker(self, worker):
        for wrk in self.workers[:]:
            if wrk == worker:
                log.write("Worker {} removed".format(worker.addr))
                worker.conn.close()
                self.workers.remove(worker)
                del worker

    def workers_connected(self):
        ''' Returns number of connected workers '''
        return len(self.workers)

if __name__ == "__main__":
    obj = Main()
    Thread( target = obj.startLoop).start()

    while (1):
        try:
            input()
        except:
            obj.shutdown()
            break