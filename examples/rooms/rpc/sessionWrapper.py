

class SessionWrapper():

    def __init__(self, session):
        self.session = session
        self.transactions = dict()

    def getSession(self):
        return self.session

    def getTransaction(self, requestId):
        return self.transactions.get(requestId)

    def addTransaction(self, requestId, transaction):
        if requestId in self.transactions.keys():
            print("Found an existing transaction for the key:", requestId)
        self.transactions[requestId] = transaction

    def removeTransaction(self, requestId):
        self.transactions.pop(requestId)

    def getTransactions(self):
        return self.transactions.values()