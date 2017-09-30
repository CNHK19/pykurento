
from pykurento import KurentoClient
from .loadManager import loadManager

class Kms():
    def __init__(self, client, kmsUri):
        self.client = client
        self.kmsUri = kmsUri
        self.loadManager = loadManager(self)

    def setLoadManager(self, loadManager):
        self.loadManager = loadManager

    def getLoad(self):
        return self.loadManager.calculateLoad()

    def allowMoreElements(self):
        return self.loadManager.allowMoreElements()

    def getUri(self):
        return self.kmsUri

    def getKurentoClient(self):
        return self.client