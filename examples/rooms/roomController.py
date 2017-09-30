
import simplejson
import tornado.web
from . import kurentoRoomServerApp

UPDATE_SPEAKER_INTERVAL_DEFAULT = 1800
THRESHOLD_SPEAKER_DEFAULT = -50

loopbackRemote = True
loopbackAndLocal = False
filterRequestParam = "marker"

class getAllRoomsHandler(tornado.web.RequestHandler):
    def get(self):
        roomManager = kurentoRoomServerApp.getRoomManager()
        self.write(simplejson.dumps(roomManager.getRooms()))

class getUpdateSpeakerIntervalHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(simplejson.dumps(dict(updateSpeakerInterval=UPDATE_SPEAKER_INTERVAL_DEFAULT)))

class getThresholdSpeakerHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(simplejson.dumps(dict(thresholdSpeaker=THRESHOLD_SPEAKER_DEFAULT)))

class getClientConfigHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(simplejson.dumps(dict(loopbackRemote=loopbackRemote, loopbackAndLocal=loopbackAndLocal, filterRequestParam=filterRequestParam)))

