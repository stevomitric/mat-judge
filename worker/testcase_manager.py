import os, json

class Testcases:
    def __init__(self, db):
        self.db = db

    def validTestcases(self, tc):
        try:
            if isinstance(tc, str):
                tc = eval(tc)

            for i in range(len(tc)):
                if (len(tc[i]) != 2):
                    return 0
                if (not isinstance(tc[i][0], str) or not isinstance(tc[i][1],str)):
                    return 0
        except:
            return 0
        return tc

    def saveTestcases(self, tc):
        ''' Saves current batch and returns id to the testcases '''

        # Check if testcases are valid
        tc = self.validTestcases(tc)
        if not tc:
            return {'error': 'Invalid testcases'}
        
        # Save to file
        id = self.db.db_testcase.add(tc)
        
        return {'testcase_id': id, 'testcases': tc}

    def loadTestcases(self, id):
        ''' Return saved testcases'''

        tc = self.db.db_testcase.get(id)
        if tc == -1:
            return {'error': 'Testcase ID is not valid'}
        else:
            return {'testcases': tc}


        
