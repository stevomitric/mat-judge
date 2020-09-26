import requests, json, time

header = {
    'Content-Type': 'application/json'
}

code = '''
#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >>b;
    cout << a +b << endl;

    return 0;
}'''
payload = {
    'code': code,
    'language': 'c++11',
    'testcases': '[("1 1", "2")]',
}
tm = time.time()
res = {}


for i in range(400000):
    res = requests.post('http://127.0.0.1:5000/api/v0/submit', headers=header, data=json.dumps(payload))

    res = json.loads(res.text)
    print (res)

print ("Completed queue in {} sec".format(round(time.time()-tm,2)))

id = res['submission_id']

#id=123132
while 1:
    res = requests.get('http://127.0.0.1:5000/api/v0/status?submission_id={}&output=1'.format(id))
    res = json.loads(res.text)
    if 'error' not in res and not res['running']:
        break
    time.sleep(.01)

print(json.dumps(res, indent=4))

print ("Completed submission in {} sec".format(round(time.time()-tm,2)))