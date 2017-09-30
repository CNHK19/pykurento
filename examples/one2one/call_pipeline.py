
from pykurento import media
from examples import kurento

from pykurento import KurentoClient

kurento = KurentoClient("ws://192.168.56.101:8888/kurento")

class CallPipeline(object):
    def __init__(self,  caller, callee):
        self.recording_path = "file:///tmp/dd"
        self.recording_ext = ".webm"

        self.pipeline = kurento.create_pipeline()

        self.webRtcCaller = media.WebRtcEndpoint(self.pipeline)
        self.webRtcCallee = media.WebRtcEndpoint(self.pipeline)
        self.recorderCaller = media.RecorderEndpoint(self.pipeline, uri=self.recording_path + "_caller" + self.recording_ext)
        self.recorderCallee = media.RecorderEndpoint(self.pipeline, uri=self.recording_path + "_callee" + self.recording_ext)

        # Connections
        self.webRtcCaller.connect(self.webRtcCallee)
        self.webRtcCaller.connect(self.recorderCaller)

        self.webRtcCallee.connect(self.webRtcCaller)
        self.webRtcCallee.connect(self.recorderCallee)

    def record(self):
        self.recorderCaller.record()
        self.recorderCallee.record()

    def generateSdpAnswerForCaller(self,sdpOffer):
        return self.webRtcCaller.processOffer(sdpOffer)

    def generateSdpAnswerForCallee(self, sdpOffer):
        return self.webRtcCallee.processOffer(sdpOffer)

    def getPipeline(self):
        return self.pipeline

    def getCallerWebRtcEp(self):
        return self.webRtcCaller

    def getCalleeWebRtcEp(self):
        return self.webRtcCallee