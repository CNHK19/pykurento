#!/usr/bin/env python

import os
import sys
import logging
import signal
import tornado.ioloop
import tornado.web
import tornado.httpserver

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
logging.getLogger().setLevel(logging.DEBUG)

from examples import render_view
import examples.loopback.handlers
import examples.rooms.roomJsonRpcHandler
import examples.rooms.roomController
import examples.call.handlers
import examples.one2one.call_handler
import examples.multires.handlers

class IndexHandler(tornado.web.RequestHandler):
  def get(self):
    render_view(self, "index")

class RoomHandler(tornado.web.RequestHandler):
  def get(self):
    render_view(self, "room")

class LoginHandler(tornado.web.RequestHandler):
  def get(self):
    render_view(self, "login")

application = tornado.web.Application([
  (r"/", RoomHandler),
  (r"/login", LoginHandler),
  (r"/loopback", examples.loopback.handlers.LoopbackHandler),
  (r"/multires", examples.multires.handlers.MultiResHandler),
  (r"/room", examples.rooms.roomJsonRpcHandler.RoomJsonRpcHandler),
  (r"/call", examples.call.handlers.CallIndexHandler),
  # (r"/call/join/(?P<room_id>\d*)", examples.rooms.handlers.JoinHandler),
  (r"/room/getAllRooms", examples.rooms.roomController.getAllRoomsHandler),
  (r"/room/getUpdateSpeakerInterval", examples.rooms.roomController.getUpdateSpeakerIntervalHandler),
  (r"/room/getThresholdSpeaker", examples.rooms.roomController.getThresholdSpeakerHandler),
  (r"/room/getClientConfig", examples.rooms.roomController.getClientConfigHandler),

  (r"/callws", examples.one2one.call_handler.CallHandler),
  # (r"/room/(?P<room_id>\d*)", examples.rooms.handlers.RoomHandler),
  # (r"/room/(?P<room_id>[^/]*)/subscribe/(?P<from_participant_id>[^/]*)/(?P<to_participant_id>[^/]*)", examples.rooms.handlers.SubscribeToParticipantHandler),
  (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(__file__), "static")}),
], debug=True)

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8080))
  http_server = tornado.httpserver.HTTPServer(application,
                                              # protocol='https',
                                              # ssl_options={
                                              #   "certfile": "/home/xunyu/Projects/pykurento/certs/development.crt",
                                              #   "keyfile": "/home/xunyu/Projects/pykurento/certs/development.key",}
                                              )
  print("Webserver now listening on port %d" % port)
  http_server.listen(port)
  tornado.ioloop.IOLoop.current().start()


  # application.listen(port)

  # ioloop = tornado.ioloop.IOLoop.instance()
  # signal.signal(signal.SIGINT, lambda sig, frame: ioloop.stop())
  # ioloop.start()
