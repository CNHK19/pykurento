
class kmsLoad():
    def __init__(self, kms, load):
        self.kms = kms
        self.load = load

    def getKms(self):
        return self.kms

    def getLoad(self):
        return self.load

    def compareTo(self, inLoad):
        if inLoad.load == self.load:
            return 0
        elif self.load < inLoad.load:
            return -1
        else:
            return 1

    def __lt__(self, other):
        return self.load < other.load


class KmsManager():

    def __init__(self):
        self.kmss = []
        self.usageIterator = None

    #TODO session if??
    def getKurentoClient(self, sessionInfo=None):
        return self.getKms(sessionInfo).getKurentoClient()

    def getKms(self, sessionInfo=None):
        if not self.usageIterator:
            self.usageIterator = iter(self.kmss)
        try:
            kms = self.usageIterator.__next__()
        except StopIteration:
            self.usageIterator = iter(self.kmss)
            kms = self.usageIterator.__next__()
        return kms

    def addKms(self, kms):
        self.kmss.append(kms)

    def getLessLoadedKms(self):
        sortedLoads = self.getKmssSortedByLoad()
        return sortedLoads[0]


    def getKmssSortedByLoad(self):
        kmsLoads = self.getKmsLoads()
        kmsLoads.sort()
        return kmsLoads

    def getKmsLoads(self):
        kmsLoads = []
        for kms in self.kmss:
            load = kms.getLoad()
            kmsLoads.append(kmsLoad(kms, load))
        return kmsLoads

    def getNextLessLoadedKms(self):
        sortedLoads = self.getKmssSortedByLoad()

        if len(sortedLoads) > 1:
            return sortedLoads[1].kms
        else:
            return sortedLoads[0].kms


    def destroyWhenUnused(self):
        pass