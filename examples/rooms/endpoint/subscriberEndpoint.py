from .mediaEndpoint import MediaEndpoint
from pykurento import media
from ..exception.roomException import Code
from .sdpType import SdpType


class SubscriberEndpoint(MediaEndpoint):

    def __init__(self, web, owner, endpointName, pipeline):
        self.connectedToPublisher = False
        self.publisher = None

        super(SubscriberEndpoint, self).__init__(web, False, owner, endpointName, pipeline, None)


    def subscribe(self, sdpOffer, publisher):

        self.registerOnIceCandidateEventListener()
        sdpAnswer = self.processOffer(sdpOffer)
        self.gatherCandidates()

        publisher.connect(self.getEndpoint())
        self.setConnectedToPublisher(True)
        self.setPublisher(publisher)
        return sdpAnswer

    def isConnectedToPublisher(self):
        return self.connectedToPublisher

    def setConnectedToPublisher(self, connectedToPublisher):
        self.connectedToPublisher = connectedToPublisher

    def getPublisher(self):
        return self.publisher

    def setPublisher(self, publisher):
        self.publisher = publisher

    def mute(self, muteType):
        if not self.publisher:
            raise(Code.MEDIA_MUTE_ERROR_CODE, "Publisher endpoint not found")

        if muteType == "AUDIO":
            self.publisher.disconnectFrom(self.getEndpoint(), media.MediaType.AUDIO)
        elif muteType == "VIDEO":
            self.publisher.disconnectFrom(self.getEndpoint(), media.MediaType.VIDEO)
        else:
            self.publisher.disconnectFrom(self.getEndpoint())

        self.resolveCurrentMuteType(muteType)

    def unmute(self):
        self.publisher.connect(self.getEndpoint())

        self.setMuteType(None)