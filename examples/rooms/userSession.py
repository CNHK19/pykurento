
class UserSession():
    def __init__(self, session, name):

        self.name = name
        self.session = session
        self.sdpOffer = ""
        self.callingTo = ""
        self.callingFrom = ""
        self.webRtcEndpoint = ""
        self.playingWebRtcEndpoint = ""
        self.candidateList = []

    def getSession(self):
        return self.session

    def getName(self):
        return self.name

    def getSdpOffer(self):
        return self.sdpOffer;

    def setSdpOffer(self, sdpOffer):
        self.sdpOffer = sdpOffer

    def getCallingTo(self):
        return self.callingTo

    def setCallingTo(self, callingTo):
        self.callingTo = callingTo

    def getCallingFrom(self):
        return self.callingFrom

    def setCallingFrom(self,callingFrom):
        self.callingFrom = callingFrom

    def sendMessage(self, message):
        self.session.write_message(message)
        pass


    def getSessionId(self):
        return self.session.getId()

    def setWebRtcEndpoint(self, webRtcEndpoint):
        self.webRtcEndpoint = webRtcEndpoint
        if self.webRtcEndpoint:
            self.webRtcEndpoint.ice_candidate_found(self.onEmptyEvent)
            for e in self.candidateList:
                self.webRtcEndpoint.add_ice_candidate(e)
            self.candidateList.clear()

    def addCandidate(self,candidate):
        if self.webRtcEndpoint:
          self.webRtcEndpoint.add_ice_candidate(candidate);
        else:
            self.candidateList.append(candidate);

        if self.playingWebRtcEndpoint:
          self.playingWebRtcEndpoint.add_ice_candidate(candidate);


    def getPlayingWebRtcEndpoint(self):
        return self.playingWebRtcEndpoint

    def setPlayingWebRtcEndpoint(self, playingWebRtcEndpoint):
        self.playingWebRtcEndpoint = playingWebRtcEndpoint

    def clear(self):
        self.webRtcEndpoint = None
        self.candidateList.clear()

    def onEmptyEvent(self):
        pass