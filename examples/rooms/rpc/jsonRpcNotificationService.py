
from .sessionWrapper import SessionWrapper
from .participantSession import SESSION_KEY
class JsonRpcNotificationService():

    def __init__(self):
        self.sessions = dict()

    def addTransaction(self, transaction, request):
        sessionId = transaction.getSession()
        sw = self.sessions.get(sessionId)
        if not sw:
            sw = SessionWrapper(transaction)
            if sessionId not in self.sessions.keys():
                print("Concurrent initialization of session wrapper #:", sessionId)
            self.sessions[sessionId]=sw
        sw.addTransaction(request['id'], transaction)
        return sw

    def getSession(self, sessionId):
        sw = self.sessions.get(sessionId)
        if not sw:
            return None

        return sw.getSession()

    def getAndRemoveTransaction(self, participantRequest):

        tid = None
        if not participantRequest:
            print("Unable to obtain a transaction for a null ParticipantRequest object")
            return None

        tidVal = participantRequest.getRequestId()
        try:
            tid = int(tidVal)
        except:
            print("Invalid transaction id, a number was expected but recv:", tidVal)
            return None

        sessionId = participantRequest.getParticipantId()
        sw = self.sessions.get(sessionId)
        if not sw:
            print("Invalid session id {%s}" % sessionId)
            return None

        print("#{%s} - {%d} transactions" % (sessionId, len(sw.getTransactions())))

        t = sw.getTransaction(tid)
        sw.removeTransaction(tid)
        return t


    def sendResponse(self, participantRequest, result):
        t = self.getAndRemoveTransaction(participantRequest)
        if not t:
            print("No transaction found for {%s}, unable to send result {%s}" % (participantRequest, result))
            return

        try:
            t.sendResponse(result)
        except Exception as e:
            print("Exception responding to user {%s}: %s" % (participantRequest, str(e)))


    def sendErrorResponse(self, participantRequest, data, error):
        t = self.getAndRemoveTransaction(participantRequest)
        if not t:
            print("No transaction found for {%s}, unable to send result {%s}" % (participantRequest, data))
            return
        #TODO
        # try:
        dataVal = None
        if data:
            dataVal = str(data)

        t.sendError(error.getCodeValue(), error.getMessage(), dataVal)
        # except:
        #     print("Exception sending error response to user (%s)" % participantRequest)

    def sendNotification(self, participantId, method, params):
        sw = self.sessions.get(participantId)
        if not sw or not sw.getSession():
            print("No session found for id {%d}, unable to send notification {%s}: {%s}" % (participantId, method, params))
            return
        s = sw.getSession()
        try:
            s.sendNotification(method, params)
        except:
            print("Exception sending notification '{%s}': {%s} to user id {%s}" % (method, params, participantId))

    def closeSession(self, participantRequest):
        if not participantRequest:
            print("No session found for null ParticipantRequest object, unable to cleanup")
            return

        sessionId = participantRequest.getParticipantId()
        sw = self.sessions.get(sessionId)
        if not sw or not sw.getSession():
            print("No session found for id {%d}, unable to cleanup" % sessionId)
            return

        s = sw.getSession()

        try:
            ps = None
            if SESSION_KEY in s.getAttributes().keys():
                ps = s.getAttributes().get(SESSION_KEY)
            s.close()
            print("Closed session for req {%s} (userInfo:{%s})" % (participantRequest, ps))
        except:
            print("Error closing session for req {%s}" % participantRequest)

        self.sessions.pop(sessionId)