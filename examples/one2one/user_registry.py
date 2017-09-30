
class UserRegistry(object):
    def __init__(self):
        self.usersByName = dict()
        self.usersBySessionId = dict()

    def register(self, session):
        self.usersByName[session.getName()] = session
        self.usersBySessionId[session.getSessionId()] = session

    def getByName(self, name):
        try:
            return self.usersByName[name]
        except:
            return None

    def getBySession(self, session_id):

        try:
            return self.usersBySessionId[session_id]
        except:
            return None

    def exists(self, name):
        if name in self.usersByName.keys():
            return True
        else:
            return False

    def removeBySession(self, session_id):
        session = self.getBySession(session_id)
        if session:
            del self.usersByName[session.getName()]
            del self.usersBySessionId[session_id]

        return session
  