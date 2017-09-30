from examples import kurento
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
import time
from pykurento import media

#
# db_config = {
#     'host': '127.0.0.1',
#     'user': 'root',
#     'passwd': '000000',
#     'db':'test',
#     'charset':'utf8'
# }
# engine = create_engine('mysql://%s:%s@%s/%s?charset=%s'%(db_config['user'],
#                                                          db_config['passwd'],
#                                                          db_config['host'],
#                                                          db_config['db'],
#                                                          db_config['charset']), echo=False)

engine = create_engine('sqlite:///calls.db', echo=False)

Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

pipeline = None

def get_pipeline():
    global pipeline
    if not pipeline:
        pipeline = kurento.create_pipeline()
    return pipeline

def get_session():
    return session


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    incoming_endpoint_id = Column(String(50))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    pipeline_id = Column(String(50))
    name = Column(String(50))

    room = relationship("Room", backref=backref('participants', order_by=id))

    def get_incoming(self):
        # if self.incoming_endpoint_id:
        #     incoming = media.WebRtcEndpoint(get_pipeline(), id=self.incoming_endpoint_id)
        # else:
        #     incoming = media.WebRtcEndpoint(get_pipeline())
        #     self.incoming_endpoint_id = incoming.id
        #     session = get_session()
        #     session.add(self)
        #     session.commit()
        incoming = media.WebRtcEndpoint(get_pipeline())
        return incoming

    def get_answer(self, offer):
        return self.get_incoming().process_offer(offer)

    def connect(self, offer):
        incoming = self.get_incoming()
        outgoing = media.WebRtcEndpoint(get_pipeline())
        incoming.connect(outgoing)
        return outgoing.process_offer(offer)

    # def get_pipeline(self):
    #   if self.pipeline_id:
    #     pipeline = kurento.get_pipeline(self.pipeline_id)
    #   else:
    #     pipeline = kurento.create_pipeline()
    #     self.pipeline_id = pipeline.id
    #     session = get_session()
    #     session.add(self)
    #     session.commit()
    #   return pipeline

    def disconnect(self):
        incoming = self.get_incoming()
        outgoing = media.WebRtcEndpoint(get_pipeline())
        incoming.disconnect(outgoing)
        self.pipeline_id = None
        session = get_session()
        session.add(self)
        session.commit()

    def record(self):
        wrtc = media.WebRtcEndpoint(get_pipeline())
        recorder = media.RecorderEndpoint(get_pipeline(), uri="file:///tmp/test.webm")
        wrtc.connect(recorder)
        recorder.record()


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(String(50))

    def on_event(self, *args, **kwargs):
        print("received event!")
        print(args)
        print(kwargs)

    def get_pipeline(self):

        if self.pipeline_id:
            pipeline = kurento.get_pipeline(self.pipeline_id)
        else:
            pipeline = kurento.create_pipeline()
            self.pipeline_id = pipeline.id
            session = get_session()
            session.add(self)
            session.commit()

        return pipeline

    def add_candidate(self, candidate):
        wrtc = media.WebRtcEndpoint(get_pipeline())
        wrtc.add_ice_candidate(candidate)


    def ice_candidate_found(self, sdp_offer):
        wrtc = media.WebRtcEndpoint(get_pipeline())
        wrtc.ice_candidate_found(self.on_event)
        wrtc.process_offer(sdp_offer)
        wrtc.gather_candidates()

    def get_candidates(self):
        wrtc = media.WebRtcEndpoint(get_pipeline())
        wrtc.gather_candidates()
        time.sleep(10)
        return kurento.get_ice_candidates()



Base.metadata.create_all(engine)
