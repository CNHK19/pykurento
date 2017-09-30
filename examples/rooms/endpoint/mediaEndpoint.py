from ..api.mutedMediaType import MutedMediaType
from ..exception.roomException import Code, RoomException
from pykurento import media

class MediaEndpoint():

    def __init__(self, web, dataChannels, owner, endpointName, pipeline, log=None):
        self.web = web
        self.dataChannels = dataChannels
        self.owner = owner
        self.setEndpointName(endpointName)
        self.setMediaPipeline(pipeline)

        self.webEndpoint = None
        self.endpoint = None

        self.endpointSubscription = None
        self.candidates = []
        self.muteType = None


    def isWeb(self):
        return self.web

    def getOwner(self):
        return self.owner

    def getEndpoint(self):
        if self.isWeb():
            return self.webEndpoint
        else:
            return self.endpoint

    def getWebEndpoint(self):
        return self.webEndpoint

    def getRtpEndpoint(self):
        return self.endpoint

    def createEndpoint(self, endpointLatch):
        old = self.getEndpoint()
        if not old:
            self.internalEndpointInitialization(endpointLatch)
        else:
            endpointLatch.countDown()

        if self.isWeb():
            while self.candidates:
                self.internalAddIceCandidate(self.candidates.pop())

        return old

    def getPipeline(self):
        return self.pipeline

    def setMediaPipeline(self, pipeline):
        self.pipeline = pipeline

    def getEndpointName(self):
        return self.endpointName

    def setEndpointName(self, endpointName):
        self.endpointName = endpointName

    def unregisterErrorListeners(self):
        self.unregisterElementErrListener(self.endpoint, self.endpointSubscription)

    def setMuteType(self, muteType):
        self.muteType = muteType

    def getMuteType(self):
        return self.muteType

    def resolveCurrentMuteType(self, newMuteType):

        prev = self.getMuteType()
        if not prev:
            if prev == MutedMediaType.ALL:
                return

            elif prev == MutedMediaType.VIDEO:
                if self.muteType == MutedMediaType.AUDIO:
                    self.setMuteType(MutedMediaType.ALL)
                    return

            elif prev == MutedMediaType.AUDIO:
                if self.muteType == MutedMediaType.VIDEO:
                    self.setMuteType(MutedMediaType.ALL)
                    return

        self.setMuteType(newMuteType)

    def internalEndpointInitialization(self, endpointLatch):
        if self.isWeb():
            self.webEndpoint = media.WebRtcEndpoint(self.pipeline)
            if self.dataChannels:
                self.webEndpoint.useDataChannels()
            #todo
            self.webEndpoint.setMaxVideoRecvBandwidth(600)
            self.webEndpoint.setMinVideoRecvBandwidth(300)
            self.webEndpoint.setMaxVideoSendBandwidth(600)
            self.webEndpoint.setMinVideoSendBandwidth(300)
            self.webEndpoint.OnIceCandidate()
            endpointLatch.countDown()

            print("EP {%s}: Created a new WebRtcEndpoint" % self.endpointName)
            self.endpointSubscription = self.registerElemErrListener(self.webEndpoint)

    def addIceCandidate(self, candidate):

        if not self.isWeb():
            raise RoomException("Operation not supported", Code.MEDIA_NOT_A_WEB_ENDPOINT_ERROR_CODE)

        if not self.webEndpoint:
            self.candidates.append(candidate)
        else:
            self.internalAddIceCandidate(candidate)

    def registerElemErrListener(self, element):
        pass

    def unregisterElementErrListener(self, element, subscription):
        pass

    def processOffer(self, offer):

        if self.isWeb():
            if not self.webEndpoint:
                raise RoomException("Can't process offer when WebRtcEndpoint is null (ep: " + self.endpointName + ")", Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE)

            return self.webEndpoint.processOffer(offer)
        else:
            if not self.endpoint:
                raise RoomException("Can't process offer when RtpEndpoint is null (ep: " + self.endpointName + ")", Code.MEDIA_RTP_ENDPOINT_ERROR_CODE)

            return self.endpoint.processOffer(offer)

    def generateOffer(self):
        if self.isWeb():
            if not self.webEndpoint:
                raise RoomException("Can't generate offer when WebRtcEndpoint is null (ep: " + self.endpointName + ")", Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE)

            return self.webEndpoint.generateOffer()
        else:
            if not self.endpoint:
                raise RoomException("Can't generate offer when RtpEndpoint is null (ep: " + self.endpointName + ")", Code.MEDIA_RTP_ENDPOINT_ERROR_CODE)

            return self.endpoint.generateOffer()

    def processAnswer(self, answer):
        if self.isWeb():
            if not self.webEndpoint:
                raise RoomException("Can't process answer  when WebRtcEndpoint is null (ep: " + self.endpointName + ")", Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE)

            return self.webEndpoint.processAnswer(answer)
        else:
            if not self.endpoint:
                raise RoomException("Can't process answer  when RtpEndpoint is null (ep: " + self.endpointName + ")", Code.MEDIA_RTP_ENDPOINT_ERROR_CODE)

            return self.endpoint.processAnswer(answer)

    def registerOnIceCandidateEventListener(self):
        pass

    def gatherCandidates(self):
        if not self.isWeb():
           return
        if not self.webEndpoint:
            raise RoomException("Can't start gathering ICE candidates on null WebRtcEndpoint(ep: " + self.endpointName + ")", Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE)

        return self.webEndpoint.gatherCandidates()

    def internalAddIceCandidate(self, candidate):
        if not self.webEndpoint:
            print (Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE,
          "Can't add existing ICE candidates to null WebRtcEndpoint (ep: " + self.endpointName + ")")

        self.webEndpoint.addIceCandidate(candidate)
