import simplejson
from pykurento import media
from pykurento.transport import KurentoTransport


class KurentoClient(object):
    def __init__(self, url, transport=None):
        self.url = url
        self.transport = transport or KurentoTransport(self.url)

    def get_transport(self):
        return self.transport

    def create_pipeline(self):
        return media.MediaPipeline(self)

    def get_pipeline(self, id):
        return media.MediaPipeline(self, id=id)

    def createMediaPipeline(self):
        return media.MediaPipeline(self)

    def get_ice_candidates(self):
        return self.transport.get_ice_candidates()

class IceCandidate(object):
    def __init__(self, candidate, sdpMid, sdpMLineIndex):
        self.candidate = candidate
        self.sdpMid = sdpMid
        self.sdpMLineIndex = sdpMLineIndex

    def serialize(self):
        return self.__dict__

    def getCandidate(self):
        return self.candidate

    def setCandidate(self,candidate):
        self.candidate = candidate

    def getSdpMid(self):
        return self.sdpMid

    def setSdpMid(self, sdpMid):
        self.sdpMid = sdpMid

    def getSdpMLineIndex(self):
        return self.sdpMLineIndex

    def setSdpMLineIndex(self, sdpMLineIndex):
        self.sdpMLineIndex = sdpMLineIndex

