''' Development DB testing module '''

import db_manager, time

db = db_manager.DB()

res = db.db_testcase.add(["1 3", "4"])
print(db.db_testcase.get('asd'))