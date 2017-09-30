from ..endpoint.publisherEndpoint import PublisherEndpoint
from ..endpoint.subscriberEndpoint import SubscriberEndpoint
from pykurento import media
from pykurento.countDownLatch import CountDownLatch
from ..exception.roomException import Code, RoomException


ASYNC_LATCH_TIMEOUT = 30

class Participant():

    def __init__(self, id, name, room, pipeline, dataChannels, web,):
        self.id = id
        self.name = name
        self.web = web
        self.dataChannels = dataChannels
        self.recorderedFileName = ""
        self.room = room
        self.pipeline = pipeline

        # self.composite = Composite(pipeline)
        # self.hubPort = HubPort(self.composite)
        self.publisher = PublisherEndpoint(web, dataChannels, self, name, pipeline)
        self.passThru = media.PassThrough(pipeline)
        self.endPointLatch = CountDownLatch(1)

        self.filters = dict()
        self.subscribers = dict()

        self.streaming = False
        self.recording = False
        self.closed = False


        for other in room.getParticipants():
            if other.getName() != name:
                self.getNewOrExistingSubscriber(other.getName())

    def createPublishingEndpoint(self):
        self.publisher.createEndpoint(self.endPointLatch)

        if not self.getPublisher().getEndpoint():
            raise RoomException("Unable to create publisher endpoint", Code.MEDIA_ENDPOINT_ERROR_CODE)

    def getId(self):
        return self.id

    def getName(self):
        return self.name

    # def getComposite(self):
    #     return self.composite

    def shapePublisherMedia(self, element, media_type=None):
        if not media_type:
            self.publisher.apply(element)
        else:
            self.publisher.apply(element, media_type)

    def getFilterElement(self, id):
        return self.filters.get(id)

    def addFilterElement(self, id, filter):
        self.filters[id] = filter

        self.shapePublisherMedia(filter, None)

    def disableFilterelement(self, filterID, releaseElement):
        filter = self.getFilterElement(filterID)
        if filter:
            try:
                self.publisher.revert(filter, releaseElement)
            except:
                pass

    def enableFilterelement(self, filterID):
        filter = self.getFilterElement(filterID)

        if filter:
            try:
                self.publisher.apply(filter)
            except:
                pass

    def removeFilterElement(self, filterID):
        filter = self.getFilterElement(filterID)

        self.filters.pop(filterID)
        if filter:
            try:
                self.publisher.revert(filter)
            except:
                pass

    def releaseAllFilters(self):
        for key in self.filters.keys():
            self.removeFilterElement(key)

    def getRecorderedFileName(self):
        return self.recorderedFileName

    def setRecorderedFileName(self, fileName):
        self.recorderedFileName = fileName

    def getPublisher(self):
        try:
            if self.endPointLatch.await(ASYNC_LATCH_TIMEOUT):
                raise RoomException("Timeout reached while waiting for publisher endpoint to be ready", Code.MEDIA_ENDPOINT_ERROR_CODE)
        except Exception as e:
            raise RoomException("Interrupted while waiting for publisher endpoint to be ready: " + str(e), Code.MEDIA_ENDPOINT_ERROR_CODE)

        return self.publisher

    def getRoom(self):
        return self.room

    def getPipeline(self):
        return self.pipeline

    def isClosed(self):
        return self.closed

    def isStreaming(self):
        return self.streaming

    def isRecording(self):
        return self.recording

    def setRecording(self, isRecording):
        self.recording = isRecording

    def isSubscribed(self):
        for se in self.subscribers.values():
            if se.isConnectedToPublisher():
                return True
        return False

    def getConnectedSubscribedEndpoints(self):
        subscribedToSet = []
        for se in self.subscribers.values():
            if se.isConnectedToPublisher():
                subscribedToSet.append(se.getEndpointName())

        return subscribedToSet

    def preparePublishConnection(self):
        print("USER {%s}: Request to publish video in room {%s} by " + "initiating connection from server" %
        self.name, self.room.getName())

        sdpOffer = self.getPublisher().preparePublishConnection()

        print("USER {%s}: Publishing SdpOffer is {%s}" % (self.name, sdpOffer))
        print("USER {%s}: Generated Sdp offer for publishing in room {%s}" % (self.name, self.room.getName()))
        return sdpOffer

    def publishToRoom(self, sdpType, sdpString, doLoopback, loopbackAlternativeSrc, loopbackConnectionType):
        print("USER {%s}: Request to publish video in room {%s} (sdp type {%s})" % (self.name, self.room.getName(), sdpType))
        print("USER {%s}: Publishing Sdp ({%s}) is {%s}" % (self.name, sdpType, sdpString))

        sdpResponse = self.getPublisher().publish(sdpType, sdpString, doLoopback, loopbackAlternativeSrc, loopbackConnectionType)

        self.streaming = True

        print("USER {%s}: Publishing Sdp ({%s}) is {%s}" % (self.name, sdpType, sdpResponse))
        print("USER {%s}: Is now publishing video in room {%s}" % (self.name, self.room.getName()))

        # self.publisher.apply(self.passThru)
        # self.passThru.connect(self.hubPort)

        return sdpResponse

    def unpublishMedia(self):
        print("PARTICIPANT {%s}: unpublishing media stream from room {%s}" % (self.name, self.room.getName()))
        self.releasePublisherEndpoint()
        self.publisher = PublisherEndpoint(self.web, self.dataChannels, self, self.name, self.pipeline)
        print("PARTICIPANT {}: released publisher endpoint and left it initialized (ready for future streaming)" % self.name)

    def receiveMediaFrom(self, sender, sdpOffer):
        senderName = sender.getName()
        print("USER {%s}: Request to receive media from {%s} in room {%s}" % (self.name, senderName, self.room.getName()))
        print("USER {%s}: SdpOffer for {%s} is {%s}" % (self.name, senderName, sdpOffer))

        if self.name == senderName:
            print("PARTICIPANT {%s}: trying to configure loopback by subscribing" % self.name)
            raise RoomException("Can loopback only when publishing media", Code.USER_NOT_STREAMING_ERROR_CODE)

        if not sender.getPublisher():
            print("PARTICIPANT {%s}: Trying to connect to a user without a publishing endpoint" %
                     self.name)
            return None

        print("PARTICIPANT {%s}: Creating a subscriber endpoint to user {%s}" % (self.name, senderName))

        subscriber = self.getNewOrExistingSubscriber(senderName)

        try:
            subscriberLatch = CountDownLatch(1)
            oldMediaEndpoint = subscriber.createEndpoint(subscriberLatch)
            try:
                if subscriberLatch.await(ASYNC_LATCH_TIMEOUT):
                    raise RoomException("Timeout reached when creating subscriber endpoint", Code.MEDIA_ENDPOINT_ERROR_CODE)

            except Exception as e:
                raise RoomException("Interrupted when creating subscriber endpoint: " + str(e), Code.MEDIA_ENDPOINT_ERROR_CODE)

            if oldMediaEndpoint:
                print("PARTICIPANT {%s}: Two threads are trying to create at the same time a subscriber endpoint for user {%s}" % (self.name, senderName))
                return None

            if not subscriber.getEndpoint():
                raise RoomException("Unable to create subscriber endpoint", Code.MEDIA_ENDPOINT_ERROR_CODE)
        except Exception as e:
            self.subscribers.pop(senderName)
            raise RoomException(str(e))

        print("PARTICIPANT {%s}: Created subscriber endpoint for user {%s}" % (self.name, senderName))

        try:
            sdpAnswer = subscriber.subscribe(sdpOffer, sender.getPublisher())
            print("USER {%s}: Subscribing SdpAnswer is {%s}" % (self.name, sdpAnswer))
            print("USER {%s}: Is now receiving video from {%s} in room {%s}" % (self.name, senderName, self.room.getName()))
            return sdpAnswer
        except Exception as e:
            print(e)
            self.subscribers.pop(senderName)
            self.releaseSubscriberEndpoint(senderName, subscriber)

        return None

    def cancelReceivingMedia(self, senderName):
        print("PARTICIPANT {%s}: cancel receiving media from {%s}" % (self.name, senderName))
        try:
            subscriberEndpoint = self.subscribers.pop(senderName)
        except:
            subscriberEndpoint = None
        if not subscriberEndpoint or not subscriberEndpoint.getEndpoint():
            print("PARTICIPANT {%s}: Trying to cancel receiving video from user {%s}. But there is no such subscriber endpoint." %(self.name, senderName))
        else:
            print("PARTICIPANT {%s}: Cancel subscriber endpoint linked to user {%s}" % (self.name, senderName))

        self.releaseSubscriberEndpoint(senderName, subscriberEndpoint)

    def mutePublishedMedia(self, muteType):
        if not muteType:
            raise RoomException("Mute type cannot be null", Code.MEDIA_MUTE_ERROR_CODE)
        self.getPublisher().mute(muteType)

    def unmutePublishedMedia(self):
        if not self.getPublisher().getMuteType():
            print("PARTICIPANT {%s}: Trying to unmute published media. But media is not muted." % self.name)
        else:
            self.getPublisher().unmute()

    def muteSubscribedMedia(self, sender, muteType):
        if not muteType:
            raise RoomException("Mute type cannot be null", Code.MEDIA_MUTE_ERROR_CODE)

        senderName = sender.getName()
        subscriberEndpoint = self.subscribers.get(senderName)

        if not subscriberEndpoint or not subscriberEndpoint.getEndpoint():
            print("PARTICIPANT {%s}: Trying to mute incoming media from user {%s}. But there is no such subscriber endpoint." % (self.name, senderName))
        else:
            print("PARTICIPANT {%s}: Mute subscriber endpoint linked to user {%s}" % (self.name, senderName))

        subscriberEndpoint.mute(muteType)

    def unmuteSubscribedMedia(self, sender):
        senderName = sender.getName()
        subscriberEndpoint = self.subscribers.get(senderName)

        if not subscriberEndpoint or not subscriberEndpoint.getEndpoint():
            print("PARTICIPANT {%s}: Trying to unmute incoming media from user {%s}. But there is no such subscriber endpoint." % (self.name, senderName))
        else:
            print("PARTICIPANT {%s}: Mute subscriber endpoint linked to user {%s}" % (self.name, senderName))

        subscriberEndpoint.unmute()

    def close(self):
        print("PARTICIPANT {%s}: Closing user" % self.name)

        if self.isClosed():
            print("PARTICIPANT {%s}: Already closed" % self.name)
            return

        self.closed = True

        for remoteParticipantName in self.subscribers.keys():
            subscriber = self.subscribers.get(remoteParticipantName)
            if subscriber and subscriber.getEndpoint():
                self.releaseSubscriberEndpoint(remoteParticipantName, subscriber)
                print("PARTICIPANT {%s}: Released subscriber endpoint to {%s}" % (self.name, remoteParticipantName))
            else:
                print("PARTICIPANT {%s}: Trying to close subscriber endpoint to {%s}. But the endpoint was never instantiated." % (self.name, remoteParticipantName))

        self.releasePublisherEndpoint()


    def getNewOrExistingSubscriber(self, remoteName):
        sendingEndpoint = SubscriberEndpoint(self.web, self, remoteName, self.pipeline)
        self.subscribers[remoteName] = sendingEndpoint
        if remoteName in self.subscribers.keys():
            print("PARTICIPANT {%s}: Already exists a subscriber endpoint to user {%s}" % (self.name, remoteName))
            sendingEndpoint = self.subscribers[remoteName]
        else:
            print("PARTICIPANT {%s}: New subscriber endpoint to user {%s}" % (self.name, remoteName))
            self.subscribers[remoteName] = sendingEndpoint

        return sendingEndpoint

    def addIceCandidate(self, endpointName, iceCandidate):
        if self.name==endpointName:
            self.publisher.addIceCandidate(iceCandidate)
        else:
            self.getNewOrExistingSubscriber(endpointName).addIceCandidate(iceCandidate)

    def sendIceCandidate(self, participantId, endpointName, candidate):
        self.room.sendIceCandidate(participantId, endpointName, candidate)

    def sendMediaError(self, event):
        pass

    def releasePublisherEndpoint(self):
        if self.publisher and self.publisher.getEndpoint():
            self.streaming = False
            self.publisher.unregisterErrorListeners()
            for el in self.publisher.getMediaElements():
                self.releaseElement(self.name, el)
            self.releaseElement(self.name, self.publisher.getEndpoint())
            self.publisher = None

        else:
            print("PARTICIPANT {%s}: Trying to release publisher endpoint but is null", self.name)

    def releaseSubscriberEndpoint(self, senderName, subscriber):
        if subscriber:
            subscriber.unregisterErrorListeners()
            self.releaseElement(senderName, subscriber.getEndpoint())
        else:
            print("PARTICIPANT {%s}: Trying to release subscriber endpoint for '{%s}' but is null" % (self.name, senderName))

    def releaseElement(self, senderName, element):
        eid = element.getId()
        try:
            element.release()
        except Exception as e:
            print("PARTICIPANT {%s}: Error calling release on elem #{%s} for {%s}" % (self.name, eid, senderName))