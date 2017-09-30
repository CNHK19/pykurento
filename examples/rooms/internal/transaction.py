
from .jsonRpcConstants import JsonRpcConstants
import simplejson

class Transaction():

    def __init__(self, session, requestId, messageWriter):
        self.session = session
        self.requestId = requestId
        self.messageWriter = messageWriter
        self.responded = False
        self.async=False
        self._responseData = dict(id=requestId, jsonrpc=JsonRpcConstants.JSON_RPC_VERSION)

    def getSession(self):
        return self.session

    def startAsync(self):
        self.async = True

    def isAsync(self):
        return self.async

    def sendResponse(self, result):
        self._internalSendResponse(result)

    def sendVoidResponse(self):
        pass

    def sendResponseObject(self, response):
        pass

    def sendError(self, code, type, message, data):
        pass

    def isNotification(self):
        pass

    def sendNotification(self, method, params):
        responseData = dict(jsonrpc=JsonRpcConstants.JSON_RPC_VERSION, method=method, params=params)
        try:
            self.messageWriter(simplejson.dumps(responseData))
        except Exception as e:
            print("Failed to send message {%s}, ERROR:{%s}" % (simplejson.dumps(responseData), str(e)))

    def _internalSendResponse(self, result=None):
        if self.responded:
            return
        if result:
            self._responseData["result"] = simplejson.loads(result)
        if self.session:
            if isinstance(self._responseData["result"], list):
                self._responseData["result"] = dict(sessionId=self.session, value=self._responseData["result"])
            else:
                self._responseData["result"]["sessionId"] = self.session
            if "value" not in self._responseData["result"].keys():
                self._responseData["result"]["value"] = []

        self.messageWriter(simplejson.dumps(self._responseData))
        self.responded = True


