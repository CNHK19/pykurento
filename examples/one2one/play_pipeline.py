from pykurento import media
from examples import kurento
import simplejson

class PlayMediaPipeline(object):
    def __init__(self, session):
        self.pipeline = None
        self.webRtc = None
        self.player = None
        self.recording_path = "file:///tmp/dd"
        self.recording_ext = ".webm"

        self.pipeline = kurento.create_pipeline()

        self.webRtc = media.WebRtcEndpoint(self.pipeline)
        self.player = media.PlayerEndpoint(self.pipeline, uri=self.recording_path + "_caller" + self.recording_ext);
        self.session = session

        # Connection
        self.player.connect(self.webRtc);

        # Player listeners
        self.player.addErrorListener(self.onErrorEvent)


    def onErrorEvent(self):
        self.sendPlayEnd(self.session)

    def sendPlayEnd(self, session):
        rtn_msg = simplejson.dumps({"id":"playEnd"})
        session.write_message(rtn_msg)

        self.pipeline.release()
        self.this.webRtc = None

    def play(self):
        self.player.play()

    def generateSdpAnswer(self,sdpOffer):
        return self.webRtc.processOffer(sdpOffer)

    def getPipeline(self):
        return self.pipeline
  
    def getWebRtc(self):
        return self.webRtc

    def getPlayer(self):
        return self.player
