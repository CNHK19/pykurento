import tornado.web
import tornado.gen
import tornado.ioloop
import tornado.websocket
from tornado.locks import Condition
from examples import render_view

import simplejson
import uuid
import time
from pykurento import media
from examples import kurento
from examples.one2one.user_session import UserSession
from examples.one2one.user_registry import UserRegistry
from examples.one2one.play_pipeline import PlayMediaPipeline
from examples.one2one.call_pipeline import CallPipeline

class CallIndexHandler(tornado.web.RequestHandler):
    def get(self):
        render_view(self, "call")


class CallHandler(tornado.websocket.WebSocketHandler):
    clients = set()
    pipelines = dict()
    user_registry = UserRegistry()

    def check_origin(self, origin):
        return True

    def getId(self):
        return self.session_id

    # def ice_candidate_found(self, sdp_offer):
    #     self.get_incoming().ice_candidate_found(self.on_event)
    #     #self.get_incoming().process_offer(sdp_offer)
    #     self.get_incoming().gather_candidates()
    #
    # def get_candidates(self):
    #     self.get_incoming().gather_candidates()
    #     time.sleep(10)
    #     return kurento.get_ice_candidates()

    def open(self, *args):

        self.session_id = uuid.uuid4()
        self.call_accept = False
        self.sdp_offer = None
        self.user_session = None
        # self.caller = None
        # self.ice_candidate = {}
        # self.send_ice_candidate = False
        # self.id = self.get_argument("Id")
        self.stream.set_nodelay(True)
        # self.incoming_endpoint_id = None
        # clients[self.id] = {"id": self.id, "object": self}
        CallHandler.clients.add(self)

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

        if id == "register":
            rtn_msg = self.register()

        elif id == "call":
            self.call()

        elif id == "incomingCallResponse":
            self.incoming_call_response()
        elif id == "play":
            rtn_msg = self.play()
        elif id == "onIceCandidate":
            self.on_ice_candidate()
        elif id == "stop":
            rtn_msg = self.stop()
        elif id == "stopPlay":
            pass

        elif "method" in message.keys():
            method = message['method']
            if method == 'leaveRoom':
                self.on_close()
                return
            self.message = message["params"]
            if method == 'publishVideo':
                pass
                # self.call()
            elif method == 'call':
                self.call()
            elif method == "register":
                self.register()
            elif method == "onIceCandidate":
                self.message = dict(candidate=message["params"])
                self.on_ice_candidate()
        if rtn_msg:
            self.write_message(rtn_msg)

        def on_close(self):
            CallHandler.clients.remove(self)
            # if self.id in clients:
            #     del clients[self.id]

    def register(self):
        try:
            name = self.message['name']
        except:
            return simplejson.dumps({"id": "registerResponse", "response": "rejected: empty user name"})

        self.user_session = UserSession(self, name)
        if CallHandler.user_registry.exists(name):
            return simplejson.dumps(
                {"id": "registerResponse", "response": "rejected: user '" + name + "' already registered"})
        else:
            CallHandler.user_registry.register(self.user_session)
            return simplejson.dumps({"id": "registerResponse", "response": "accepted"})
            # else:
            #     return simplejson.dumps({"id": "registerResponse", "response": "rejected: user '" + name + "' already registered"})

    @tornado.gen.coroutine
    def call(self):

        if 'from' not in self.message.keys():
            if 'to' not in self.message.keys():
                self.write_message(simplejson.dumps(
                    {"id": "callResponse", "response": "rejected", "message": "To user missed"}))
                return
            else:
                to_user = self.message['to']
                for user_name in CallHandler.user_registry.usersByName.keys():
                    if self.user_session == CallHandler.user_registry.usersByName[user_name]:
                        from_user = user_name
        else:
            try:
                from_user = self.message['from']
                to_user = self.message['to']
            except:
                for user_name in CallHandler.user_registry.usersByName.keys():
                    if self.user_session != CallHandler.user_registry.usersByName[user_name]:
                        to_user = user_name
                    else:
                        from_user = user_name
                self.write_message(simplejson.dumps(
                    {"id": "callResponse", "response": "rejected", "message": "from or to error"}))
                return

        sdp_offer = None

        try:
            sdp_offer = self.message['sdpOffer']
        except:
            self.write_message(simplejson.dumps(
                {"id": "callResponse", "response": "rejected", "message": "sdpOffer missed"}))
            return

        # self.ice_candidate_found(sdp_offer)
        self.user_session.ice_candidate_found(sdp_offer)
        if CallHandler.user_registry.exists(to_user):
            self.user_session.setSdpOffer(sdp_offer)
            self.user_session.setCallingTo(to_user)
            rtn_msg = simplejson.dumps({"id": "incomingCall", "from": from_user})

            callee = CallHandler.user_registry.getByName(to_user)
            callee.sendMessage(rtn_msg)
            callee.setCallingFrom(self.user_session)
            # while not clients[client_id].call_accept:
            #     print ("Client wait time:",  time_count)
            #     if time_count > time_out:
            #         return simplejson.dumps(
            #             {"id": "callResponse", "response": "rejected", "message": "user not accept call"})
            # io_loop = tornado.ioloop.IOLoop.current()
            #
            # yield call_condition.wait(timeout=io_loop.time() + 30)
            # if not to_participant.call_accept:
            #     self.write_message(simplejson.dumps(
            #         {"id": "callResponse", "response": "rejected", "message": "user not accept call"}))
            # else:
            #
            #     # room.ice_candidate_found(sdp_offer)
            #     # sdp_answer = from_participant.connect(sdp_offer)
            #     # # sdp_answer = from_participant.get_answer(sdp_offer)
            #     self.record()
            #     # sdp_answer = self.get_answer(sdp_offer)
            #     sdp_answer = self.connect(sdp_offer)
            #     # ice_cadidates = room.get_candidates()
            #     # for candidate in ice_cadidates:
            #     #     rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
            #     #         {"candidate": candidate['candidate'],
            #     #          "sdpMid": candidate['sdpMid'],
            #     #          "sdpMLineIndex": candidate['sdpMLineIndex']}})
            #     #     self.write_message(rtn_msg)
            #     self.write_message( simplejson.dumps(
            #         {"id": "callResponse", "response": "accepted", "sdpAnswer": sdp_answer}))
            return

        else:
            self.write_message(
                simplejson.dumps({"id": "callResponse", "response": "rejected", "message": "to user not found"}))

    def on_ice_candidate(self):
        try:
            candidate = self.message['candidate']
        except:
            return simplejson.dumps({"id": "onIceCandidate", "response": "rejected: candidate information missed"})

        # for client_id in clients.keys():
        #     if clients[client_id] is not self:
        #         rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate": candidate})
        #         clients[client_id].write_message(rtn_msg)
        self.user_session.addCandidate(candidate)

    @tornado.gen.coroutine
    def incoming_call_response(self):

        try:
            from_user = self.message['from']
            sdp_offer = self.message['sdpOffer']
            call_response = self.message['callResponse']
        except:
            self.write_message(simplejson.dumps({"id": "callResponse", "response": "rejected: parameter missed"}))
            return

        if call_response == 'accept':
            # self.call_accept = True
            caller = CallHandler.user_registry.getByName(from_user)
            callMediaPipeline = CallPipeline(from_user, self.user_session.getName())
            CallHandler.pipelines[caller.getSessionId()] = callMediaPipeline.getPipeline()
            CallHandler.pipelines[self.user_session.getSessionId()] = callMediaPipeline.getPipeline()

            self.user_session.setWebRtcEndpoint(callMediaPipeline.getCalleeWebRtcEp())
            calleeSdpAnswer = callMediaPipeline.generateSdpAnswerForCallee(sdp_offer)
            self.write_message(simplejson.dumps({"id": "startCommunication", "from": from_user, "sdpAnswer": calleeSdpAnswer}))
            # from_participant = None
            #
            # for client in CallHandler.clients:
            #     if from_user == client.user_name:
            #         from_participant = client

            # sdp_answer = self.user_session.get_answer(sdp_offer)
            # self.ice_candidate_found(sdp_offer)
            # call_condition.notify()
            # ice_cadidates = room.get_candidates()
            # for candidate in ice_cadidates:
            #
            #     rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
            #                             {"candidate": candidate['candidate'],
            #                              "sdpMid":candidate['sdpMid'],
            #                              "sdpMLineIndex": candidate['sdpMLineIndex']}})
            #     self.write_message(rtn_msg)
            # self.send_ice_candidate = True
            # self.ice_candidate_worker()
            # self.write(simplejson.dumps({"id": "startCommunication", "sdpAnswer": sdp_answer}))

            callMediaPipeline.getCalleeWebRtcEp().gather_candidates()
            yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 3)
            ice_candidates = callMediaPipeline.getCalleeWebRtcEp().get_ice_candidates()
            for ice_candidate in ice_candidates:
                rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
                    {"candidate": ice_candidate['candidate'],
                     "sdpMid": ice_candidate['sdpMid'],
                     "sdpMLineIndex": ice_candidate['sdpMLineIndex']}})
                self.write_message(rtn_msg)

            callerSdpOffer = CallHandler.user_registry.getByName(from_user).getSdpOffer()
            caller.setWebRtcEndpoint(callMediaPipeline.getCallerWebRtcEp())
            callerSdpAnswer = callMediaPipeline.generateSdpAnswerForCaller(callerSdpOffer)
            rtn_msg = simplejson.dumps({"id": "callResponse", "response": "accepted", "sdpAnswer": callerSdpAnswer})
            caller.sendMessage(rtn_msg)

            callMediaPipeline.getCallerWebRtcEp().gatherCandidates()
            yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 1)
            ice_candidates = callMediaPipeline.getCallerWebRtcEp().get_ice_candidates()
            for ice_candidate in ice_candidates:
                rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
                    {"candidate": ice_candidate['candidate'],
                     "sdpMid": ice_candidate['sdpMid'],
                     "sdpMLineIndex": ice_candidate['sdpMLineIndex']}})
                caller.sendMessage(rtn_msg)

            callMediaPipeline.record()

            return
        else:
            # call_condition.notify()
            self.write_message(simplejson.dumps({"id": "callResponse", "response": "rejected: parameter missed"}))

    @tornado.gen.coroutine
    def ice_candidate_worker(self):

        while True:
            yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 3)
            if self.send_ice_candidate:
                ice_cadidates = self.get_candidates()
                # for key in ice_cadidates.keys():
                #     for client in CallHandler.clients:
                #         if key in client.ice_candidate:
                #             continue
                #         rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
                #             {"candidate": ice_cadidates[key]['candidate'],
                #              "sdpMid": ice_cadidates[key]['sdpMid'],
                #              "sdpMLineIndex": ice_cadidates[key]['sdpMLineIndex']}})
                #         client.write_message(rtn_msg)
                for candidate in ice_cadidates:
                    for client in CallHandler.clients:
                        rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate":
                            {"candidate": candidate['candidate'],
                             "sdpMid": candidate['sdpMid'],
                             "sdpMLineIndex": candidate['sdpMLineIndex']}})
                        client.write_message(rtn_msg)

    def stop(self):
        stopperUser = CallHandler.user_registry.getBySession(self.user_session.getSessionId());
        if stopperUser and (stopperUser.getCallingFrom() or stopperUser.getCallingTo()):
            # self.disconnect(self.caller)
            # self.send_ice_candidate = False
            stopperUser.clear()
            return simplejson.dumps({"id": "stopCommunication"})

    def releasePipeline(self):
        sessionId = self.user_session.getSessionId()

        if sessionId in CallHandler.pipelines.keys():
            CallHandler.pipelines[sessionId].release()
            CallHandler.pipelines.pop(sessionId, None)

            self.user_session.setWebRtcEndpoint(None)
            self.user_session.setPlayingWebRtcEndpoint(None)

            # set to null the endpoint of the other user

            stoppedUser = self.user_session.getCallingFrom()
            if stoppedUser:
                stoppedUser.setWebRtcEndpoint(None)
                stoppedUser.setPlayingWebRtcEndpoint(None)

            stoppedUser = self.user_session.getCallingTo()
            if stoppedUser:
                stoppedUser.setWebRtcEndpoint(None)
                stoppedUser.setPlayingWebRtcEndpoint(None)

    def play(self):
        try:
            user = self.message['user']
            sdpOffer = self.message['sdpOffer']
        except:
            return simplejson.dumps({"id": "playResponse", "response": "rejected", "error": "user name error"})

        if not CallHandler.user_registry.exists(user):
            return simplejson.dumps(
                {"id": "playResponse", "response": "rejected", "error": "No recording for user '" + user
                                                                        + "'. Please type a correct user in the 'Peer' field."})

        playMediaPipeline = PlayMediaPipeline(self.user_session.getSession())

        self.user_session.setPlayingWebRtcEndpoint(playMediaPipeline.getWebRtc())

        sdpAnswer = playMediaPipeline.generateSdpAnswer(sdpOffer)

        rtn_msg = simplejson.dumps({"id": "playResponse", "response": "accepted", "sdpAnswer": sdpAnswer})

        playMediaPipeline.play()
        CallHandler.pipelines[self.user_session.getSessionId()] = playMediaPipeline.getPipeline()

        self.user_session.sendMessage(rtn_msg)
        playMediaPipeline.getWebRtc().gatherCandidates()
