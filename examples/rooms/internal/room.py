from time import gmtime, strftime
from ..exception.roomException import Code, RoomException
from pykurento.client import KurentoClient
from ..internal.participant import Participant
from pykurento.countDownLatch import CountDownLatch
from pykurento.media import *

ASYNC_LATCH_TIMEOUT = 30

class Room():


    def __init__(self, roomName, kurentoClient, roomHandler, destroyKurentoClient):
        self.participants = dict()
        self.name = roomName
        self.pipeline = ""
        self.pipelineLatch = CountDownLatch(1)
        self.kurentoClient = kurentoClient
        self.roomHandler = roomHandler
        self.recorder = ""
        self.closed = False
        self.activePublishers = None
        self.pipelineReleased = False
        self.destroyKurentoClient = destroyKurentoClient
        self.pipelineCreateLock = False
        self.filterStates = dict()


    def _checkClosed(self):
        if self.closed:
            print(Code.ROOM_CLOSED_ERROR_CODE, "The room '" + self.name + "' is closed")
        return self.closed

    def getName(self):
        return self.name

    def getPipeline(self):
        return self.pipeline

    def _createPipeline(self):
        if self.pipeline:
            return None

        try:
            self.pipeline = self.kurentoClient.create_pipeline()
            print("ROOM {%s}: Created MediaPipeline" % self.name)
        except:
            print("Unable to create media pipeline for room" % self.name)

    def join(self, participantId, userName, dataChannels, webParticipant):

        if self._checkClosed():
            return

        if not userName:
            print(Code.GENERIC_ERROR_CODE, "Empty user name is not allowed")
            return

        for p in self.participants.keys():
            if self.participants[p].name == userName:
                print(Code.EXISTING_USER_IN_ROOM_ERROR_CODE, "User '" + userName + "' already exists in room '" + self.name + "'")
                return

        self._createPipeline()

        participant = Participant(participantId, userName, self, self.getPipeline(), dataChannels, webParticipant)
        self.participants[participantId] = participant

        for filterId in self.filterStates.keys():
            self.roomHandler.updateFilter(self.name, participant, filterId, self.filterStates[filterId])

        print("ROOM {%s}: Added participant {%s}" % (self.name, userName))


    def newPublisher(self, participant):
        self.registerPublisher()

        for participant1 in self.participants.values():
            if participant == participant1:
                continue

            participant1.getNewOrExistingSubscriber(participant.getName())

        print("ROOM {%s}: Virtually subscribed other participants {%s} to new publisher {%s}" % (self.name,
            self.participants.values(), participant.getName()))

    def cancelPublisher(self, participant):
        self.deregisterPublisher()

        for subscriber in self.participants.values():
            if participant == subscriber:
                continue

            subscriber.cancelReceivingMedia(participant.getName())

        print("ROOM {%s}: Unsubscribed other participants {%s} from the publisher {%s}" % (self.name,
            self.participants.values(), participant.getName()))

    def leave(self, participantId):
        self.checkClosed()

        participant = self.participants.get(participantId)

        if not participant:
            raise RoomException("User #" + participantId + " not found in room '" + self.name + "'", Code.USER_NOT_FOUND_ERROR_CODE)

        participant.releaseAllFilters()

        if participant.isRecording():
            self.stopRecording(participantId)

        print("PARTICIPANT {%s}: Leaving room {%s}" % (participant.getName(), self.name))

        if participant.isStreaming():
            self.deregisterPublisher()

        self.removeParticipant(participant)
        participant.close()

    def getParticipants(self):
        self.checkClosed()
        return self.participants.values()

    def getParticipantIds(self):
        self.checkClosed()
        return self.participants.keys()

    def getParticipant(self, participantId):
        self.checkClosed()
        return self.participants.get(participantId)

    def getParticipantByName(self, userName):
        self.checkClosed()
        for p in self.participants.values():
            if userName == p.getName():
                return p
        return None

    def close(self):
        if not self.closed:
            for user in self.participants.values():
                user.close()

            self.participants.clear()
            self.closePipeline()

            print("Room {%s} closed" % self.name)

            if self.destroyKurentoClient:
                self.kurentoClient.destroy()

            self.closed = True

        else:
            print("Closing an already closed room '{%s}'" % self.name)

    def sendIceCandidate(self, participantId, endpointName, candidate):
        self.roomHandler.onIceCandidate(self.name, participantId, endpointName, candidate['candidate'], candidate['sdpMLineIndex'], candidate['sdpMid'])

    def sendMediaError(self, participantId, description):
        self.roomHandler.onMediaElementError(self.name, participantId, description)

    def isClosed(self):
        return self.closed

    def checkClosed(self):
        if self.closed:
            raise RoomException("The room '" + self.name + "' is closed", Code.ROOM_CLOSED_ERROR_CODE)

    def removeParticipant(self, participant):
        self.checkClosed()

        self.participants.pop(participant.getId())

        print("ROOM {%s}: Cancel receiving media from user '{%s}' for other users" % (self.name, participant.getName()))

        for other in self.participants.values():
            other.cancelReceivingMedia(participant.getName())


    def getActivePublishers(self):
        pass

    def registerPublisher(self):
        pass

    def deregisterPublisher(self):
        pass

    def createPipeline(self):

        if self.pipeline:
            return

        print("ROOM {%s}: Creating MediaPipeline" % self.name)

        try:
            self.kurentoClient.createMediaPipeline()
        except:
            pass
        self.pipelineLatch.countDown()

        if self.getPipeline():
            raise RoomException( "Unable to create media pipeline for room '" + self.name + "'", Code.ROOM_CANNOT_BE_CREATED_ERROR_CODE)

        # self.pipeline.addErrorListener()

    def closePipeline(self):
        if self.pipeline or self.pipelineReleased:
            return

        self.pipeline = None

    def updateFilter(self, filterId):
        state = self.filterStates.get(filterId)
        newState = self.roomHandler.getNextFilterState(filterId, state)

        self.filterStates[filterId] = newState

        for participant in self.participants.values():
            self.roomHandler.updateFilter(self.getName(), participant, filterId, newState)

    def recordSession(self, participantId):
        RECORDING_EXT = ".webm"
        TXT_EXTENSION = ".txt"
        RECORDING_PATH = "file:///tmp/kurento/"
        pipeline = self.getPipeline()
        recordInitiator = self.getParticipant(participantId)

        now = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
        filePath = RECORDING_PATH + now + "/" + recordInitiator.getName() + RECORDING_EXT

        # composite = recordInitiator.getComposite()
        # profile = MediaProfileSpecType.WEBM
        self.recorder = RecorderEndpoint(self.getPipeline(), uri=filePath).withMediaProfile()
        # recorderHubPort = HubPort(composite)
        # recorderHubPort.connect(recorder)
        self.recorder.record()

        recordInitiator.setRecording(True)


    def stopRecording(self, participantId):
        self.recorder.stop()
        self.recorder = None
        participant = self.getParticipant(participantId)
        participant.setRecording(False)
        participant.setRecorderedFileName("")



