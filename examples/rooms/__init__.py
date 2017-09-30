
from .rpc.jsonRpcUserControl import JsonRpcUserControl
from .rpc.jsonRpcNotificationService import JsonRpcNotificationService

from .kms.kmsManager import KmsManager
from .notificationRoomManager import NotificationRoomManager

from .kms.kms import Kms
from pykurento import KurentoClient, media

MSS_URIS_PROPERTY = "kms.uris"
KMSS_URIS_DEFAULT = "ws://192.168.56.101:8888/kurento"

class KurentoRoomServerApp():

    def __init__(self):
        self.notificationService = JsonRpcNotificationService()
        self.kmsManager = KmsManager()
        self.kmsManager.addKms(Kms(KurentoClient(KMSS_URIS_DEFAULT), KMSS_URIS_DEFAULT))
        self.roomManager = NotificationRoomManager(self.notificationService , self.kmsManager)
        self.userControl = JsonRpcUserControl(self.roomManager)

    def getNotificationService(self):
        return self.notificationService

    def getKmsManager(self):
        return self.kmsManager

    def getRoomManager(self):
        return self.roomManager

    def getUserControl(self):
        return self.userControl

    def setNotificationService(self, notificationService):
        self.notificationService = notificationService

    def setKmsManager(self, kmsManager):
        self.kmsManager = kmsManager

    def setRoomManager(self, roomManager):
        self.roomManager = roomManager

    def setUserControl(self, userControl):
        self.userControl = userControl


kurentoRoomServerApp = KurentoRoomServerApp()