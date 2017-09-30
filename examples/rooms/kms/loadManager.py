


class loadManager():
    def __init__(self, kms):
        self.kms = kms
        self.maxWebRtcPerKms = 0

    def MaxWebRtcLoadManager(self, maxWebRtcPerKms):
        self.maxWebRtcPerKms = maxWebRtcPerKms

    def calculateLoad(self):
        numWebRtcs = self.__countWebRtcEndpoints(self.kms)
        if numWebRtcs > self.maxWebRtcPerKms:
            return 1
        else:
            return numWebRtcs / self.maxWebRtcPerKms

    def allowMoreElements(self, kms):
        return self.__countWebRtcEndpoints(kms) < self.maxWebRtcPerKms

    def __countWebRtcEndpoints(self, kms):
        try:
            return kms.getKurentoClient().getServerManager().getPipelines().size()
        except:
            raise("Error counting KurentoClient pipelines")



