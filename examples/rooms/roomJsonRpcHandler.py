import tornado.web
import tornado.websocket
from .rpc.jsonRpcUserControl import JsonRpcUserControl
from .rpc.jsonRpcNotificationService import JsonRpcNotificationService

import tornado.gen

from . import models
from .userSession import UserSession
from .userRegistry import UserRegistry
from .internal.transaction import Transaction
from .internal.protocolElements import ProtocolElements
from .internal.jsonRpcConstants import JsonRpcConstants
from .api.pojo.participantRequest import ParticipantRequest

import tornado.ioloop
import tornado.websocket
from tornado.locks import Condition
from examples import render_view
from examples.call import models
import simplejson
import uuid
import time
import threading
import os, base64
from . import kurentoRoomServerApp
from pykurento.helper import timing


session = models.get_session()
call_condition = Condition()


class RoomJsonRpcHandler(tornado.websocket.WebSocketHandler):
    HANDLER_THREAD_NAME = "handler"
    clients = set()
    pipelines = dict()
    user_registry = UserRegistry()


    def __init__(self, application, request, **kwargs):
        self.notificationService = kurentoRoomServerApp.getNotificationService()
        self.kmsManager = kurentoRoomServerApp.getKmsManager()
        self.roomManager = kurentoRoomServerApp.getRoomManager()
        self.userControl = kurentoRoomServerApp.getUserControl()

        super(RoomJsonRpcHandler, self).__init__(application, request, **kwargs)


    def check_origin(self, origin):
        return True

    def getId(self):
        return self.session_id

    # def ice_candidate_found(self, sdp_offer):
    #     wrtc = media.WebRtcEndpoint(get_pipeline())
    #     wrtc.ice_candidate_found(self.on_event)
    #     wrtc.process_offer(sdp_offer)
    #     wrtc.gather_candidates()
    #
    # def get_candidates(self):
    #     wrtc = media.WebRtcEndpoint(get_pipeline())
    #     wrtc.gather_candidates()
    #     time.sleep(10)
    #     return kurento.get_ice_candidates()

    def open(self, *args):

        self.session_id = base64.b64encode(os.urandom(16))
        self.call_accept = False
        self.sdp_offer = None
        self.user_session = None
        # self.caller = None
        self.ice_candidate = {}
        # self.send_ice_candidate = False
        # self.id = self.get_argument("Id")
        self.stream.set_nodelay(True)
        # self.incoming_endpoint_id = None

        RoomJsonRpcHandler.clients.add(self)

    @timing
    def on_message(self, message):
        """
        when we receive some message we want some message handler..
        for this example i will just print message to console
        """
        print("Client received a message : %s" % message)
        # room = session.query(models.Room)
        # room.delete()

        rtn_msg = ""

        try:
            message = simplejson.loads(message)
            id = message['id']
            self.message = message
        except:
            return

        # if id == "register":
        #     rtn_msg = self.register()
        #
        # elif id == "call":
        #     self.call()
        #
        # elif id == "incomingCallResponse":
        #     self.incoming_call_response()
        # elif id == "play":
        #     rtn_msg = self.play()
        # elif id == "onIceCandidate":
        #     self.on_ice_candidate()
        # elif id == "stop":
        #     rtn_msg = self.stop()
        # elif id == "stopPlay":
        #     pass
        transaction = Transaction(self.session_id, int(id), self.write_message)
        self.notificationService.addTransaction(transaction, message)

        participantRequest = ParticipantRequest(self.session_id, int(id))

        if "method" in message.keys():
            method = message['method']
            try:
                params = message['params']
            except:
                params = None

            if method == ProtocolElements.JOINROOM_METHOD:
                self.userControl.joinRoom(transaction, params, participantRequest)
            elif method == ProtocolElements.PUBLISHVIDEO_METHOD:
                self.userControl.publishVideo(transaction, params, participantRequest)
                self.userControl.getIceCandidates(transaction, params, participantRequest)
                # self.ice_candidate_worker()
            elif method == ProtocolElements.UNPUBLISHVIDEO_METHOD:
                self.userControl.unpublishVideo(transaction, params, participantRequest)
            elif method == ProtocolElements.RECEIVEVIDEO_METHOD:
                self.userControl.getIceCandidates(transaction, params, participantRequest)
                self.userControl.receiveVideoFrom(transaction, params, participantRequest)
                # self.ice_candidate_worker()
            elif method == ProtocolElements.UNSUBSCRIBEFROMVIDEO_METHOD:
                self.userControl.unsubscribeFromVideo(transaction, params, participantRequest)
            elif method == ProtocolElements.ONICECANDIDATE_METHOD:
                self.userControl.onIceCandidate(transaction, params, participantRequest)
                self.on_ice_candidate()
            elif method == ProtocolElements.LEAVEROOM_METHOD:
                pass
                # todo in on_close
                # self.userControl.leaveRoom(transaction, params, participantRequest)
            elif method == ProtocolElements.SENDMESSAGE_ROOM_METHOD:
                self.userControl.sendMessage(transaction, params, participantRequest)
            elif method == ProtocolElements.ONPAINTSEND_METHOD:
                self.userControl.paintSend(transaction, params, participantRequest)
            elif method == ProtocolElements.CUSTOMREQUEST_METHOD:
                self.userControl.customRequest(transaction, params, participantRequest)
            elif method == ProtocolElements.RECORD_REQUEST_METHOD:
                self.userControl.recordSession(transaction, params, participantRequest)
            elif method == ProtocolElements.JOINROOM_REGISTER_PARAM:
                self.register(params)
            elif method == ProtocolElements.CALL_METHOD:
                self.userControl.call(transaction, params, participantRequest)
            elif method == ProtocolElements.PING_METHOD:
                self.ping_pong(message)
            else:
                print("Unrecognized request {%s}" % message)


    def on_close(self):
        transaction = Transaction(self.session_id, 9999, self.write_message)
        self.notificationService.addTransaction(transaction, dict(id=9999, message="Abnomal Leave Room"))
        participantRequest = ParticipantRequest(self.session_id, 9999)
        self.userControl.leaveRoom(transaction, None, participantRequest)
        RoomJsonRpcHandler.clients.pop()


    def ping_pong(self, message):

        try:
            del(message['method'])
            del(message['params'])
        except:
            pass

        message['result'] = dict(value=ProtocolElements.PONG_METHOD)
        self.write_message(simplejson.dumps(message))

    def register(self, params):
        try:
            name = params[ProtocolElements.JOINROOM_REGISTER_NAME]
        except:
            return simplejson.dumps({"id": "registerResponse", "response": "rejected: empty user name"})

        self.user_session = UserSession(self, name)
        if RoomJsonRpcHandler.user_registry.exists(name):
            self.write_message(simplejson.dumps(
                {"id": "registerResponse", "response": "rejected: user '" + name + "' already registered"}))
        else:
            RoomJsonRpcHandler.user_registry.register(self.user_session)
            self.write_message(simplejson.dumps({"id": "registerResponse", "response": "accepted"}))
            # else:
            #     return simplejson.dumps({"id": "registerResponse", "response": "rejected: user '" + name + "' already registered"})


    # def register(self):
    #     try:
    #         name = self.message['name']
    #     except:
    #         return simplejson.dumps({"id": "registerResponse", "response": "rejected: empty user name"})
    #
    #     room = session.query(models.Room).get(1)
    #     if not room:
    #         room = models.Room(id=1)
    #         session.add(room)
    #         session.commit()
    #
    #     participant = session.query(models.Participant).filter(models.Participant.name == name).first()
    #
    #     if not participant:
    #         participant = models.Participant(name=name, room_id=1)
    #         session.add(participant)
    #         session.commit()
    #
    #     self.user_id = participant.id
    #
    #     return simplejson.dumps({"id": "registerResponse", "response": "accepted"})
        # else:
        #     return simplejson.dumps({"id": "registerResponse", "response": "rejected: user '" + name + "' already registered"})

    @tornado.gen.coroutine
    def call(self, params):

        try:
            sender = params['sender']
            to_user = params['to']
        except:
            return simplejson.dumps(
                {"id": "callResponse", "response": "rejected", "message": "from or to error"})

        try:
            sdp_offer = params['sdpOffer']
        except:
            return simplejson.dumps(
                {"id": "callResponse", "response": "rejected", "message": "sdpOffer missed"})

        room = session.query(models.Room).get(1)
        if not room:
            room = models.Room(id=1)
            session.add(room)
            session.commit()
        room.ice_candidate_found(sdp_offer)

        from_participant = session.query(models.Participant).filter(models.Participant.name == from_user).first()
        to_participant = session.query(models.Participant).filter(models.Participant.name == to_user).first()

        if from_participant and to_participant:
            self.sdp_offer = sdp_offer
            for client in RoomJsonRpcHandler.clients:
                if (client is not self) and (client.user_id == to_participant.id):
                    rtn_msg = simplejson.dumps({"id": "incomingCall", "from": sender})
                    client.write_message(rtn_msg)

                    client.caller = self

                    # while not clients[client_id].call_accept:
                    #     print ("Client wait time:",  time_count)
                    #     if time_count > time_out:
                    #         return simplejson.dumps(
                    #             {"id": "callResponse", "response": "rejected", "message": "user not accept call"})
                    io_loop = tornado.ioloop.IOLoop.current()

                    yield call_condition.wait(timeout=io_loop.time() + 30)
                    if not client.call_accept:
                        self.write_message(simplejson.dumps(
                            {"id": "callResponse", "response": "rejected", "message": "user not accept call"}))
                    else:

                        # room.ice_candidate_found(sdp_offer)
                        # sdp_answer = from_participant.connect(sdp_offer)
                        # # sdp_answer = from_participant.get_answer(sdp_offer)
                        from_participant.record()
                        sdp_answer = from_participant.get_answer(sdp_offer)
                        # ice_cadidates = room.get_candidates()
                        # for candidate in ice_cadidates:
                        #     rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
                        #         {"candidate": candidate['candidate'],
                        #          "sdpMid": candidate['sdpMid'],
                        #          "sdpMLineIndex": candidate['sdpMLineIndex']}})
                        #     self.write_message(rtn_msg)
                        self.write_message(simplejson.dumps(
                            {"id": "callResponse", "response": "accepted", "sdpAnswer": sdp_answer}))

        else:
            return simplejson.dumps({"id": "callResponse", "response": "rejected", "message": "to user not found"})

    # def get_candidates(self):
    #     self.get_incoming().gather_candidates()
    #     time.sleep(10)
    #     return kurento.get_ice_candidates()

    def on_ice_candidate(self):
        ice_candidate = None
        try:
            candidate = self.message['params']
        except:
            return simplejson.dumps({"id": "onIceCandidate", "response": "rejected: candidate information missed"})

        self.ice_candidate[candidate['candidate']] = candidate
        rtn_msg =dict(id=self.message['id'], jsonrpc=self.message['jsonrpc'], result=dict(sessionId=self.session_id, value={}))

        self.write_message(simplejson.dumps(rtn_msg))



    def incoming_call_response(self):
        try:
            from_user = self.message['from']
            sdp_offer = self.message['sdpOffer']
            call_response = self.message['callResponse']
        except:
            return simplejson.dumps({"id": "callResponse", "response": "rejected: parameter missed"})

        room = session.query(models.Room).get(1)
        if not room:
            room = models.Room(id=1)
            session.add(room)
            session.commit()

        if call_response == 'accept':
            self.call_accept = True
            self.sdp_offer = sdp_offer
            from_participant = session.query(models.Participant).get(self.user_id)
            sdp_answer = from_participant.connect(sdp_offer)
            room.ice_candidate_found(sdp_offer)
            call_condition.notify()
            # ice_cadidates = room.get_candidates()
            # for candidate in ice_cadidates:
            #
            #     rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
            #                             {"candidate": candidate['candidate'],
            #                              "sdpMid":candidate['sdpMid'],
            #                              "sdpMLineIndex": candidate['sdpMLineIndex']}})
            #     self.write_message(rtn_msg)
            self.send_ice_candidate = True
            self.ice_candidate_worker()
            return simplejson.dumps({"id": "startCommunication", "sdpAnswer": sdp_answer})

        else:
            call_condition.notify()
            return simplejson.dumps({"id": "callResponse", "response": "rejected: parameter missed"})

    # @tornado.gen.coroutine
    # def ice_candidate_worker(self):
    #     yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 3)
    #     for client in RoomJsonRpcHandler.clients:
    #
    #         for candidate in client.ice_candidate:
    #             yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 0.1)
    #             rtn_msg = simplejson.dumps(dict(jsonrpc=JsonRpcConstants.JSON_RPC_VERSION, method="iceCandidate",
    #                                             params=client.ice_candidate[candidate]))
    #
    #             client.write_message(rtn_msg)


    def play(self):
        pass


    def stop(self):
        room = session.query(models.Room).get(1)
        participants = session.query(models.Participant).filter(models.Participant.room_id == 1)
        for participant in participants:
            participant.disconnect()
        self.send_ice_candidate = False
        return simplejson.dumps({"id": "stopCommunication"})


    def joinRoom(self):
        print(self.message)
        try:
            roomName = self.message.get(ProtocolElements.JOINROOM_ROOM_PARAM)
            userName = self.message.get(ProtocolElements.JOINROOM_USER_PARAM)

        except:
            return simplejson.dumps({"id": "callResponse", "response": "rejected: parameter missed"})

        dataChannels = False

        if ProtocolElements.JOINROOM_DATACHANNELS_PARAM in self.message.keys():
            dataChannels = bool(self.message.get(ProtocolElements.JOINROOM_DATACHANNELS_PARAM))

        participantSession = self.getParticipantSession(transaction)


