import logging

logger = logging.getLogger(__name__)


# This is the object graph as described at http://www.kurento.org/docs/5.0.3/mastering/kurento_API.html
# We dont mimic it precisely yet as its still being built out, not all abstractions are necessary
#                   MediaObject
# Hub               MediaElement                MediaPipeline
#          HubPort    Endpoint    Filter

class MediaType(object):
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    DATA = "DATA"


class MediaObject(object):
    def __init__(self, parent, **args):
        self.parent = parent
        self.options = args
        if 'id' in args:
            logger.debug("Creating existing %s with id=%s", self.__class__.__name__, args['id'])
            self.id = args['id']
        else:
            logger.debug("Creating new %s", self.__class__.__name__)
            self.id = self.get_transport().create(self.__class__.__name__, **args)

    def get_transport(self):
        return self.parent.get_transport()

    def get_pipeline(self):
        return self.parent.get_pipeline()

    # todo: remove arguments that have a value of None to let optional params work seamlessly
    def invoke(self, method, **args):
        return self.get_transport().invoke(self.id, method, **args)

    def subscribe(self, event, fn=None):
        def _callback(value):
            if fn:
                fn(value, self)

        return self.get_transport().subscribe(self.id, event, _callback)

    def release(self):
        return self.get_transport().release(self.id)

    def get_ice_candidates(self):
        return self.get_transport().get_ice_candidates()


class MediaPipeline(MediaObject):
    def get_pipeline(self):
        return self


class MediaElement(MediaObject):
    def __init__(self, parent, **args):
        args["mediaPipeline"] = parent.get_pipeline().id
        super(MediaElement, self).__init__(parent, **args)

    def connect(self, sink, mediaType=None):
        return self.invoke("connect", sink=sink.id)


    def disconnect(self, sink):
        return self.invoke("disconnect", sink=sink.id)

    def set_audio_format(self, caps):
        return self.invoke("setAudioFormat", caps=caps)

    def set_video_format(self, caps):
        return self.invoke("setVideoFormat", caps=caps)

    def get_source_connections(self, media_type):
        return self.invoke("getSourceConnections", mediaType=media_type)

    def get_sink_connections(self, media_type):
        return self.invoke("getSinkConnections", mediaType=media_type)


# ENDPOINTS

class UriEndpoint(MediaElement):
    def get_uri(self):
        return self.invoke("getUri")

    def pause(self):
        return self.invoke("pause")

    def stop(self):
        return self.invoke("stop")


class PlayerEndpoint(UriEndpoint):
    def play(self):
        return self.invoke("play")

    def on_end_of_stream_event(self, fn):
        return self.subscribe("EndOfStream", fn)

    def add_error_listener(self, fn):
        return

    def addErrorListener(self, fn):
        return


class RecorderEndpoint(UriEndpoint):

    def __init__(self, parent, **args):
        args["mediaPipeline"] = parent.get_pipeline().id
        args["mediaProfile"] = "WEBM"
        super(RecorderEndpoint, self).__init__(parent, **args)

    def record(self):
        return self.invoke("record")

    def stop_and_wait(self):
        return self.invoke("stop")


    def withMediaProfile(self, mediaProfile=None):
        self.mediaProfile = mediaProfile
        return self


    def stopOnEndOfStream(self):
        self.stopOnEndOfStream = True


class SessionEndpoint(MediaElement):
    def on_media_session_started_event(self, fn):
        return self.subscribe("MediaSessionStarted", fn)

    def on_media_session_terminated_event(self, fn):
        return self.subscribe("MediaSessionTerminated", fn)


class HttpEndpoint(SessionEndpoint):
    def get_url(self):
        return self.invoke("getUrl")


class HttpGetEndpoint(HttpEndpoint):
    pass


class HttpPostEndpoint(HttpEndpoint):
    def on_end_of_stream_event(self, fn):
        return self.subscribe("EndOfStream", fn)


class SdpEndpoint(SessionEndpoint):
    def generate_offer(self):
        return self.invoke("generateOffer")

    def processOffer(self, offer):
        return self.invoke("processOffer", offer=offer)

    def process_offer(self, offer):
        return self.invoke("processOffer", offer=offer)

    def processAnswer(self, answer):
        return self.invoke("processAnswer", answer=answer)

    def process_answer(self, answer):
        return self.invoke("processAnswer", answer=answer)

    def get_local_session_descriptor(self):
        return self.invoke("getLocalSessionDescriptor")

    def get_remote_session_descriptor(self):
        return self.invoke("getRemoteSessionDescriptor")

    def gather_candidates(self):
        return self.invoke("gatherCandidates")

    def gatherCandidates(self):
        return self.invoke("gatherCandidates")

    def add_ice_candidate(self, candidate):
        return self.invoke("addIceCandidate", candidate=candidate)

    def addIceCandidate(self, candidate):
        return self.invoke("addIceCandidate", candidate=candidate)

    def ice_candidate_found(self):
        return self.invoke("IceCandidateFound")

    def IceCandidateFound(self, fn):
        return self.invoke("IceCandidateFound")


class RtpEndpoint(SdpEndpoint):
    pass


class WebRtcEndpoint(SdpEndpoint):

    def __init__(self, parent, **args):
        self._useDataChannels = False
        self.certificateKeyType = None
        args["mediaPipeline"] = parent.get_pipeline().id
        super(SdpEndpoint, self).__init__(parent, **args)

    def useDataChannels(self):
        self._useDataChannels = True

    def withCertificateKeyType(self, certificateKeyType):
        self.withCertificateKeyType = certificateKeyType

    def IceGatheringDone(self):
        return self.invoke("IceGatheringDone")

    def OnIceCandidate(self):
        return self.subscribe("OnIceCandidate")

    def closeDataChannel(self, channelId):
        return self.invoke("closeDataChannel", candidate=channelId)

    def createDataChannel(self, label=None, ordered=None, maxPacketLifeTime=None, maxRetransmits=None, protocol=None):
        return self.invoke("closeDataChannel", label=label, ordered=ordered, maxPacketLifeTime=maxPacketLifeTime,
                           maxRetransmits=maxRetransmits, protocol=protocol)

    def getChildren(self):
        return self.invoke("getChildren")

    def getChilds(self):
        return self.invoke("getChilds")

    def getConnectionState(self):
        return self.invoke("getConnectionState")

    def getCreationTime(self):
        return self.invoke("getCreationTime")

    def getICECandidatePairs(self):
        return self.invoke("getICECandidatePairs")

    def getIceConnectionState(self):
        return self.invoke("getIceConnectionState")

    def getMaxAudioRecvBandwidth(self):
        return self.invoke("getMaxAudioRecvBandwidth")

    def getMaxOuputBitrate(self):
        return self.invoke("getMaxOuputBitrate")

    def getMaxOutputBitrate(self):
        return self.invoke("getMaxOutputBitrate")

    def getMaxVideoRecvBandwidth(self):
        return self.invoke("getMaxVideoRecvBandwidth")

    def getMaxVideoSendBandwidth(self):
        return self.invoke("getMaxVideoSendBandwidth")

    def getMediaPipeline(self):
        return self.invoke("getMediaPipeline")

    def getMediaState(self):
        return self.invoke("getMediaState")

    def getMinOuputBitrate(self):
        return self.invoke("getMinOuputBitrate")

    def getMinOutputBitrate(self):
        return self.invoke("getMinOutputBitrate")

    def getMinVideoRecvBandwidth(self):
        return self.invoke("getMinVideoRecvBandwidth")

    def getMinVideoSendBandwidth(self):
        return self.invoke("getMinVideoSendBandwidth")

    def getName(self):
        return self.invoke("getName")

    def getParent(self):
        return self.invoke("getParent")

    def getRembParams(self):
        return self.invoke("getRembParams")

    def getSendTagsInEvents(self):
        return self.invoke("getSendTagsInEvents")

    def getStunServerAddress(self):
        return self.invoke("getStunServerAddress")

    def getStunServerPort(self):
        return self.invoke("getStunServerPort")

    def getTurnUrl(self):
        return self.invoke("getTurnUrl")

    def setMaxAudioRecvBandwidth(self, maxAudioRecvBandwidth):
        return self.invoke("setMaxAudioRecvBandwidth", maxAudioRecvBandwidth=maxAudioRecvBandwidth)

    def setMaxOuputBitrate(self, maxOuputBitrate):
        return self.invoke("setMaxOuputBitrate", maxOuputBitrate=maxOuputBitrate)

    def setMaxVideoRecvBandwidth(self, maxVideoRecvBandwidth):
        return self.invoke("setMaxVideoRecvBandwidth", maxVideoRecvBandwidth=maxVideoRecvBandwidth)

    def setMaxVideoSendBandwidth(self, maxVideoSendBandwidth):
        return self.invoke("setMaxVideoSendBandwidth", maxVideoSendBandwidth=maxVideoSendBandwidth)

    def setMinOuputBitrate(self, minOuputBitrate):
        return self.invoke("setMinOuputBitrate", minOuputBitrate=minOuputBitrate)

    def setMinOutputBitrate(self, minOutputBitrate):
        return self.invoke("setMinOutputBitrate", minOutputBitrate=minOutputBitrate)

    def setMinVideoRecvBandwidth(self, minVideoRecvBandwidth):
        return self.invoke("setMinVideoRecvBandwidth", minVideoRecvBandwidth=minVideoRecvBandwidth)

    def setMinVideoSendBandwidth(self, minVideoSendBandwidth):
        return self.invoke("setMinVideoSendBandwidth", minVideoSendBandwidth=minVideoSendBandwidth)

    def setName(self, name):
        return self.invoke("setName", name=name)

    def setRembParams(self, rembParams):
        return self.invoke("setRembParams", rembParams=rembParams)

    def setSendTagsInEvents(self, sendTagsInEvents):
        return self.invoke("setSendTagsInEvents", sendTagsInEvents=sendTagsInEvents)

    def setStunServerAddress(self, stunServerAddress):
        return self.invoke("setStunServerAddress", stunServerAddress=stunServerAddress)

    def setStunServerPort(self, stunServerPort):
        return self.invoke("setStunServerPort", stunServerPort=stunServerPort)

    def setTurnUrl(self, turnUrl):
        return self.invoke("setTurnUrl", turnUrl=turnUrl)


class PassThrough(MediaElement):

    def __init__(self, parent, **args):
        args["mediaPipeline"] = parent.get_pipeline().id
        super(PassThrough, self).__init__(parent, **args)


# FILTERS

class GStreamerFilter(MediaElement):
    pass


class FaceOverlayFilter(MediaElement):
    def set_overlayed_image(self, uri, offset_x, offset_y, width, height):
        return self.invoke("setOverlayedImage", uri=uri, offsetXPercent=offset_x, offsetYPercent=offset_y,
                           widthPercent=width, heightPercent=height)


class ZBarFilter(MediaElement):
    def on_code_found_event(self, fn):
        return self.subscribe("CodeFound", fn)


# HUBS
class HubPort(MediaElement):
    def __init__(self, parent, **args):
        super(HubPort, self).__init__(parent, **args)


class Composite(MediaElement):
    pass


class Dispatcher(MediaElement):
    pass


class DispatcherOneToMany(MediaElement):
    pass

