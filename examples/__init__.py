import os
import sys
import codecs
base_path = os.path.dirname(__file__)

sys.path.append(os.path.abspath(os.path.join(base_path, '..')))


from pykurento import KurentoClient

kurento = KurentoClient("ws://192.168.56.101:8888/kurento")

def render_view(handler, name):
  with codecs.open("%s/views/%s.html" % (base_path, name), "r", "utf8") as f:
    handler.finish(f.read())
