from .mediaEndpoint import MediaEndpoint
from pykurento import media
from ..exception.roomException import Code
from .sdpType import SdpType

class PublisherEndpoint(MediaEndpoint):

    def __init__(self, web, dataChannels, owner, endpointName, pipeline,  log=None):
        self.passThru = None
        self.passThruSubscription = None

        self.elements = dict()
        self.elementIds = []
        self.elementsErrorSubscriptions = dict()
        self.connected = False

        super(PublisherEndpoint, self).__init__(web, dataChannels, owner, endpointName, pipeline, log)

    def internalEndpointInitialization(self, endpointLatch):
        super(PublisherEndpoint, self).internalEndpointInitialization(endpointLatch)
        self.passThru = media.PassThrough(self.getPipeline())
        self.passThruSubscription = self.registerElemErrListener(self.passThru)

    def unregisterErrorListeners(self):
        super(PublisherEndpoint, self).unregisterErrorListeners()
        self.unregisterElementErrListener(self.passThru, self.passThruSubscription)

        for elemId in self.elementIds:
            self.unregisterElementErrListener(self.elements.get(elemId), self.elementsErrorSubscriptions[elemId])

    def getMediaElements(self):
        if self.passThru:
            self.elements[self.passThru] = self.passThru
        return self.elements.values()

    def publish(self, sdpType, sdpString, doLoopback, loopbackAlternativeSrc, loopbackConnectionType):
        self.registerOnIceCandidateEventListener()
        if doLoopback:
            if not loopbackAlternativeSrc:
                self.connect(self.getEndpoint(), loopbackConnectionType)
            else:
                self.connectAltLoopbackSrc(loopbackAlternativeSrc, loopbackConnectionType)
        else:
            self.innerConnect()

        sdpResponse = ""

        if sdpType == SdpType.OFFER:
            sdpResponse = self.processOffer(sdpString)
        elif sdpType == SdpType.ANSWER:
            sdpResponse = self.processAnswer(sdpString)
        else:
            raise(Code.MEDIA_SDP_ERROR_CODE, "Sdp type not supported: " + sdpType)


        self.gatherCandidates()
        return sdpResponse

    def preparePublishConnection(self):
        return self.generateOffer()

    def connect(self, sink, media_type=None):
        if not self.connected:
            self.innerConnect()

        self.internalSinkConnect(self.passThru, sink, media_type)

    def disconnectFrom(self, sink, media_type=None):
        self.internalSinkDisconnect(self.passThru, sink, media_type)

    def apply(self, shaper, media_type=None):
        id = shaper.id
        if not id:
            raise(Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE, "Unable to connect media element with null id")

        if id in self.elements.keys():
            raise(Code.MEDIA_WEBRTC_ENDPOINT_ERROR_CODE, "This endpoint already has a media element with id " + id)

        first = None
        if self.elementIds:
            first = self.elements[0]

        if self.connected:
            if first:
                self.internalSinkConnect(first, shaper, type)

            else:
                self.internalSinkConnect(self.getEndpoint(), shaper, type)

            self.internalSinkConnect(shaper, self.passThru, type)

        self.elementIds.insert(0,id)
        self.elements[id] = shaper
        self.elementsErrorSubscriptions[id] = self.registerElemErrListener(shaper)
        return id

    def revert(self, shaper, releaseElement=True):
        elementId = shaper.id
        if elementId not in self.elements.keys():
            raise(Code.MEDIA_ENDPOINT_ERROR_CODE,"This endpoint (" + self.getEndpointName() + ") has no media element with id " + elementId)

        element = self.elements.pop(elementId)
        self.unregisterElementErrListener(element, self.elementsErrorSubscriptions.pop(elementId))

        if self.connected:
            nextId = self.getNext(elementId)
            prevId = self.getPrevious(elementId)

            prev = None
            next = None

            if nextId:
                next = self.elements.get(nextId)
            else:
                next = self.getEndpoint()

            if prevId:
                prev = self.elements.get(prevId)
            else:
                prev = self.passThru

            self.internalSinkConnect(next, prev)

        self.elementIds.remove(elementId)

        if releaseElement:
            element.release()

    def mute(self, muteType):
        sink = self.passThru

        if self.elements:
            sinkId = self.elementIds[-1]
            if sinkId in self.elements.keys():
                raise(Code.MEDIA_ENDPOINT_ERROR_CODE, "This endpoint (" + self.getEndpointName() + ") has no media element with id " + sinkId
                + " (should've been connected to the internal ep)")

            sink = self.elements.get(sinkId)

        else:
            print("Will mute connection of WebRTC and PassThrough (no other elems)")

        if muteType == "AUDIO":
            self.internalSinkDisconnect(self.getEndpoint(), sink, media.MediaType.AUDIO)
        elif muteType == "VIDEO":
            self.internalSinkDisconnect(self.getEndpoint(), sink, media.MediaType.VIDEO)
        else:
            self.internalSinkDisconnect(self.getEndpoint(), sink)

        self.resolveCurrentMuteType(muteType)


    def unmute(self):
        sink = self.passThru

        if self.elements:
            sinkId = self.elementIds[-1]
            if sinkId in self.elements.keys():
                raise(Code.MEDIA_ENDPOINT_ERROR_CODE, "This endpoint (" + self.getEndpointName() + ") has no media element with id " + sinkId
                + " (should've been connected to the internal ep)")

            sink = self.elements.get(sinkId)

        else:
            print("Will mute connection of WebRTC and PassThrough (no other elems)")

        self.setMuteType(None)
        self.internalSinkConnect(self.getEndpoint(), sink)


    def getNext(self, uid):
        try:
            idx = self.elementIds.index(uid)
        except:
            return None

        if idx + 1 == len(self.elementIds):
            return None

        return self.elementIds[idx+1]

    def getPrevious(self, uid):
        try:
            idx = self.elementIds.index(uid)
        except:
            return None

        if idx - 1 < 0:
            return None

        return self.elementIds[idx-1]

    def connectAltLoopbackSrc(self, loopbackAlternativeSrc, loopbackConnectionType):
        if not self.connected:
            self.innerConnect()

        self.internalSinkConnect(loopbackAlternativeSrc, self.getEndpoint(), loopbackConnectionType)

    def innerConnect(self):
        if not self.getEndpoint():
            raise(Code.MEDIA_ENDPOINT_ERROR_CODE, "Can't connect null endpoint (ep: " + self.getEndpointName() + ")")

        current = self.getEndpoint()
        try:
            prevId = self.elementIds[-1]
        except:
            prevId = None

        while prevId:
            prev = self.elements.get(prevId)
            if not prev:
                raise(Code.MEDIA_ENDPOINT_ERROR_CODE, "No media element with id " + prevId + " (ep: " + self.getEndpointName() + ")")

            self.internalSinkConnect(current, prev)
            current = prev
            prevId = self.getPrevious(prevId)
        self.connected = True
        self.internalSinkConnect(current, self.passThru)


    def internalSinkConnect(self, source, sink, media_type=None):
        source.connect(sink, media_type)

    def internalSinkDisconnect(self, source, sink, media_type=None):
        source.disconnect(sink, media_type)

