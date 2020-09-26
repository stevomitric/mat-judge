import os, string, random, time, subprocess, sys

from mod.default import log
from subprocess import check_output
from threading import Thread

from grader_default import judge as judge_fun_default

# Global constants
SANDBOX         = 'sandbox/'

# Global wariables
WORKLOAD = 0

def init_sandbox():
    ''' Do all preparations to the sandbox '''
    if 'sandbox' not in os.listdir(os.getcwd()):
        os.mkdir('sandbox')

def randomString(stringLength=8):
    letters = string.ascii_lowercase + string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def __save_file(f, d = '', m = 'w'):
    fl = open(f, m)
    fl.write(d)
    fl.close()

def __read_file(f, m = 'r'):
    try:
        fl = open(f, m)
        data = fl.read()
        fl.close()
    except:
        return -1
    return data

def __rem_file(f):
    try:
        os.remove(f)
        return 0
    except:
        return 1

def __flush_sandbox():
    os.system('rm -rf sandbox/*')

def is_testing(id):
    ''' Returns a boolean value representing if submission is in testing phase '''
    return not '_completed' in os.listdir('sandbox/{}'.format(id))

def testcases_judged(id):
    ''' Returns an int of how much test cases have been tested so far '''
    r = 0
    for f in os.listdir('sandbox/{}'.format(id)):
        if f.startswith('_testcase'):
            r += 1
    return r//3

def testcases_data(id):
    ''' Returns test cases status. Call only after judge has finished testing. '''
    data, i = [], 0
    while 1:
        fdata = __read_file('sandbox/{}/_testcase_{}'.format(id, i) )
        fdata_tm = __read_file('sandbox/{}/_testcase_{}_time'.format(id, i) )
        fdata_out = __read_file('sandbox/{}/_testcase_{}_output'.format(id, i) )
        if fdata == -1:
            break

        # Get judge msg
        if ' ' in fdata:
            judge_msg = fdata.split(' ', 1)[1]
        else:
            judge_msg = ''

        data.append([fdata.split(' ')[0], fdata_tm, fdata_out[0:100] + int(len(fdata_out)>100)*"..." , judge_msg])
        i += 1
    return data

def get_max_time(data):
    if not data:
        return 0
    return max([int(i[1]) for i in data ])

def get_code(data):
    codes = [i[0] for i in data]
    trig = ['WA', 'TLE', 'MLE', 'RE']
    for t in trig:
        if t in codes: return t
    return 'AC'

def get_failed_tc(data, code):
    codes = [i[0] for i in data]
    return codes.index(code)

def get_state(sub):
    id = sub['submission_id']
    try:
        context = {'running': is_testing(id), 'judged': testcases_judged(id) }
    except: return {'error': 'Invalid submission ID'}

    if __read_file('sandbox/{}/_compiler_error'.format(id)) != -1:
        context['error'] = __read_file('sandbox/{}/_compiler'.format(id))
        context['code'] = 'CE'

    elif not context['running']:
        context['output'] = testcases_data(id)
        #compiler_output = __read_file('sandbox/{}_compiler'.format(id))
        context['run_time'] = get_max_time(context['output'])
        #context['memory_used'] = 0
        context['code'] = get_code(context['output'])
        if context['code'] != 'AC':
            context['testcase'] = get_failed_tc(context['output'], context['code'])
        
        
        if 'output' not in sub or not sub['output']:
            context.pop('output')

    return context

def matching(judge_fun, inp, data1, data2):
    try:
        return judge_fun(inp, data1, data2)
    except Exception as e:
        return (0, 'Judge script failed: '+ str(e))

def compile_gpp(id, y='11'):
    r = os.system('g++ -std=c++{} -o sandbox/{}/main sandbox/{}/main.cpp 2> sandbox/{}/_compiler'.format(y, id, id, id) )
    return r

def compile_gcc(id):
    r = os.system('g++ -o sandbox/{}/main sandbox/{}/main.cpp 2> sandbox/{}/_compiler'.format(id, id, id) )
    return r

def run_program(id, t_lim = 1.0, m_lim = 256):
    #cmd = 'sandbox/{} < sandbox/{}_in > sandbox/{}_out'.format(id, id, id).split(' ')
    cmd = 'ulimit -v {}; sandbox/{}/main'.format(m_lim*1000, id)
    try:
        process = subprocess.Popen(cmd,
                            stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT,shell=True )
        wdata = __read_file('sandbox/{}/_in'.format(id), m='rb')
        process.stdin.write(wdata + b'\n')
        process.stdin.flush()
    except Exception as e:
        print (e)
        return -2

    t = time.time()
    try:
        process.wait(t_lim)
        data = process.stdout.read()
    except:
        #log.write("{} Timed out on TC".format(id))
        process.terminate()
        return -1

    # Check for seg fault
    if 'Segmentation fault' in data.decode():
        return -2
    # Check for MLE
    if 'failed to map segment from shared object' in data.decode():
        return -3

    __save_file('sandbox/{}/_out'.format(id), data.decode())

    return time.time()-t

def test_cpp(id, submission, clang = False):
    global WORKLOAD
    WORKLOAD += 1

    __save_file('sandbox/{}/main.cpp'.format(id), submission['code'])
    
    year = ''.join([i for i in submission['language'] if i in '0123456789'  ])

    if clang:
        r = compile_gcc(id)
    else:
        r = compile_gpp(id, year)
    
    if r:
        __save_file('sandbox/{}/_compiler_error'.format(id))
        __save_file('sandbox/{}/_completed'.format(id))
        WORKLOAD -= 1
        return -1

    if 'grader.py' in os.listdir('sandbox/{}'.format(id)):
        sys.path.append(os.getcwd()+'/sandbox/{}'.format(id))
        try:
            # pylint: disable-all
            from grader import judge as judge_fun
        except Exception as e:
            __save_file('sandbox/{}/_compiler_error'.format(id))
            __save_file('sandbox/{}/_completed'.format(id))
            __save_file('sandbox/{}/_compiler'.format(id), 'Importing grader failed: ' + str(e))
            sys.path.pop()
            WORKLOAD -= 1
            return -1
        sys.path.pop()

    else:
        judge_fun = judge_fun_default

        

    for i, testcase in enumerate( submission['testcases'] ):
        if len(testcase) < 2:
            writeCE(id, 'Testcase: {} has only input values'.format(i) )
            break

        __rem_file('sandbox/{}/_in'.format(id))
        __rem_file('sandbox/{}/_out'.format(id))

        __save_file('sandbox/{}/_in'.format(id), testcase[0])
        tl = run_program(id, t_lim=submission['time_limit']/1000.0, m_lim=submission['memory_limit'])
        fdata = __read_file('sandbox/{}/_out'.format(id))
        failed = 1
        #print(tl, fdata, failed)
        # Write testcase state
        if tl == -1:
            __save_file('sandbox/{}/_testcase_{}'.format(id, i), 'TLE')
        elif fdata == -1 or tl == -2:
            __save_file('sandbox/{}/_testcase_{}'.format(id, i), 'RE')
        elif tl == -3:
            __save_file('sandbox/{}/_testcase_{}'.format(id, i), 'MLE')
        elif matching(judge_fun, testcase[0], fdata, testcase[1])[0]:
            judge_msg = matching(judge_fun, testcase[0], fdata, testcase[1])[1]
            __save_file('sandbox/{}/_testcase_{}'.format(id, i), 'AC '+ judge_msg)
            failed = 0
        else:
            #print ('asd')
            judge_msg = matching(judge_fun, testcase[0], fdata, testcase[1])[1]
            __save_file('sandbox/{}/_testcase_{}'.format(id, i), 'WA ' + judge_msg)

        # Fix tl if TLE, MLE, RE
        if tl in [-1]: tl = submission['time_limit']/1000.0
        if tl in [-2, -3]: tl = 0

        # Write testcase time
        __save_file('sandbox/{}/_testcase_{}_time'.format(id, i), str(int(tl*1000)) )
        # Write output
        if fdata == -1: fdata = ''
        __save_file('sandbox/{}/_testcase_{}_output'.format(id, i), fdata )

        #time.sleep(0.1)

        # If testcase is not AC, no need to run the rest
        if (failed):
            break

    __save_file('sandbox/{}/_completed'.format(id))
    WORKLOAD -= 1

def isValidGrader(grader):
    if 'import' in grader or 'exec' in grader or 'eval' in grader:
        return 0
    return 1

def writeCE(id, error):
    __save_file('sandbox/{}/_compiler_error'.format(id))
    __save_file('sandbox/{}/_compiler'.format(id), error)
    __save_file('sandbox/{}/_completed'.format(id))

def submit( submission ):
    ''' Create a submission. subbmission argument should follow Worker#1.1 '''

    # Create a submission ID and folder
    id = submission['submission_id']
    try:
        os.mkdir('sandbox/{}'.format(id))
    except:
        return {'error': 'Submission id already exists'}

    # Write the grader script inside
    if submission['grader'] and isValidGrader(submission['grader']):
        __save_file('sandbox/{}/grader.py'.format(id), submission['grader'] )

    if submission['language'] in ['c++11', 'c++14', 'c++17']:
        Thread( target = test_cpp, args = (id, submission, )).start()
    elif lang == 'c11':
        Thread( target = test_cpp, args = (id, submission, True )).start()
    
    return {
        'submission_id': id,
    }
