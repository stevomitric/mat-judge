
import json, string, random, time

class Token:
    def __init__(self, db):
        self.db = db

    def tokenInformation(self, token):
        token_data = self.db.db_token.get(token)
        if not token_data:
            return (0, "Token doesn't exist")
        if token_data['expiration'] < time.time():
            return (0, "Token has expired")
        return (1, token_data)

    def deleteToken(self, token = '', owner = ''):
        if not token and not owner:
            return (0, 'One field must be provided')
        if token:
            self.db.db_token.removeToken(token)
            return (1, 'Removed all instances of: '+token)
        else:
            self.db.db_token.removeOwner(owner)
            return (1, "Removed all owner tokens: "+owner)

    def validateRequest(self, request):
        # Required fields
        req = ['owner', 'access_level']
        for field in req:
            if field not in request:
                return (0, 'Field "{}" is required'.format(field))

        # Set expiration default value
        try:
            request['expiration'] = int(request['expiration'])
        except:
            request['expiration'] = -1

        # check for access_level
        try:
            request['access_level'] = int(request['access_level'])
        except:
            return (0, 'Access level must be an integer')

        return (1, request)

    def createToken(self, owner, duration, access):
        token = ''.join( [ string.ascii_letters[random.randint(0,26+26-1)] for i in range(64) ] )
        if duration == -1:
            duration = 9999999999999999
        else:
            duration = time.time()+duration
        self.db.db_token.add(token,owner,access,duration)
        return token

    def validateToken(self, token, access_level):
        if not self.db.getConf()[1]:
            return (1, 'Token access turned off')

        token_data = self.db.db_token.get(token)

        if not token:
            return (0, 'Token must be specified')
        if not token_data:
            return (0, 'Invalid token')
        if access_level < token_data['access_level']:
            return (0, 'Token has insufficient permissions')
        if (token_data['expiration'] < time.time()):
            return (0, 'Token has expired')

        return (1, 'Valid token')