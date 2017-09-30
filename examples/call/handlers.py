import tornado.web
import tornado.gen
import tornado.ioloop
import tornado.websocket
from tornado.locks import Condition
from examples import render_view
from examples.call import models
import simplejson
import uuid
import time
import threading

session = models.get_session()
call_condition = Condition()

class CallIndexHandler(tornado.web.RequestHandler):
    def get(self):
        render_view(self, "call")

class CallHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def open(self, *args):
        # self.sched = TornadoScheduler()
        # self.sched.add_job(self.worker, 'interval', seconds=3)
        # self.sched.start()

        self.message = ""
        self.session_id = uuid.uuid4()
        self.call_accept = False
        self.sdp_offer = None
        self.caller = None
        self.user_id = None
        self.ice_candidate = {}
        self.send_ice_candidate = False
        # self.id = self.get_argument("Id")
        self.stream.set_nodelay(True)
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
        session.commit()
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
            rtn_msg = self.incoming_call_response()
        elif id == "play":
            pass
        elif id == "onIceCandidate":
            self.on_ice_candidate()
        elif id == "stop":
            rtn_msg = self.stop()
        elif id == "stopPlay":
            pass

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

        room = session.query(models.Room).get(1)
        if not room:
            room = models.Room(id=1)
            session.add(room)
            session.commit()

        participant = session.query(models.Participant).filter(models.Participant.name == name).first()

        if not participant:
            participant = models.Participant(name=name, room_id=1)
            session.add(participant)
            session.commit()

        self.user_id = participant.id

        return simplejson.dumps({"id": "registerResponse", "response": "accepted"})
        # else:
        #     return simplejson.dumps({"id": "registerResponse", "response": "rejected: user '" + name + "' already registered"})

    @tornado.gen.coroutine
    def call(self):

        try:
            from_user = self.message['from']
            to_user = self.message['to']
        except:
            return simplejson.dumps(
                {"id": "callResponse", "response": "rejected", "message": "from or to error"})

        try:
            sdp_offer = self.message['sdpOffer']
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
            for client in CallHandler.clients:
                if (client is not self) and (client.user_id == to_participant.id):
                    rtn_msg = simplejson.dumps({"id": "incomingCall", "from": from_user})
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

    def on_ice_candidate(self):
        try:
            candidate = self.message['candidate']
        except:
            return simplejson.dumps({"id": "onIceCandidate", "response": "rejected: candidate information missed"})
        room = session.query(models.Room).get(1)
        if not room:
            room = models.Room(id=1)
            session.add(room)
            session.commit()
        # for client_id in clients.keys():
        #     if clients[client_id] is not self:
        #         rtn_msg = simplejson.dumps({"id": "iceCandidate", "candidate": candidate})
        #         clients[client_id].write_message(rtn_msg)
        room.add_candidate(candidate)

        self.ice_candidate[candidate['candidate'].split()[0]] = candidate

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

    @tornado.gen.coroutine
    def ice_candidate_worker(self):
        room = session.query(models.Room).get(1)
        while True:
            yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 3)
            if self.send_ice_candidate:
                ice_cadidates = room.get_candidates()
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
                                                 "sdpMid":candidate['sdpMid'],
                                                 "sdpMLineIndex": candidate['sdpMLineIndex']}})
                        client.write_message(rtn_msg)


    def stop(self):
        room = session.query(models.Room).get(1)
        participants = session.query(models.Participant).filter(models.Participant.room_id == 1)
        for participant in participants:
            participant.disconnect()
        self.send_ice_candidate = False
        return simplejson.dumps({"id": "stopCommunication"})


class SubscribeToParticipantHandler(tornado.web.RequestHandler):
    def post(self, room_id, from_participant_id, to_participant_id):
        sdp_offer = self.request.body
        from_participant = session.query(models.Participant).get(from_participant_id)
        to_participant = session.query(models.Participant).get(to_participant_id)

        if from_participant and to_participant:
            sdp_answer = from_participant.connect(sdp_offer)
            self.finish({"answer": sdp_answer})
        else:
            self.set_status(409)
            self.finish({"error": "participants matching ids not found"})
