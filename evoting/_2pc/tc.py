import socket
from _2pc.util import encodeDict, decodeDict

MAX_PACKET_SIZE = 1024

class TC:
    def __init__(self, tc_addr, cohort_addr):
        self.cohort_addr = cohort_addr
        self.counter = 0
        self.hostId = str(cohort_addr)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(tc_addr)
        self.socket.settimeout(5)
        self.current = {}
        print("TC listening on port  {}...".format(tc_addr[1]))

    def run(self, actionId, arg_key, arg_val) -> bool:
        res = self.prepare(actionId, arg_key, arg_val)
        if res:
            self.commit()
        else:
            self.abort()
        return res

    def prepare(self, actionId, arg_key, arg_val):
        transactionId = self.transactionId()
        print("TC run phase1 prepare, tId=%s"%(transactionId))
        self.current = { \
            "2pc": "prepare", \
            "transactionId": transactionId, \
            "actionId": actionId, \
            "arg_key": arg_key, \
            "arg_val": arg_val \
            }
        self.socket.sendto(encodeDict(self.current), self.cohort_addr)
        try:
            recv_raw = self.socket.recv(MAX_PACKET_SIZE)
            recv = decodeDict(recv_raw)
            recv_transactionId = recv["transactionId"]
            res = recv["2pc"]
            if transactionId==recv_transactionId and res=="yes":
                return True
            else:
                return False
        except: # timeout
            return False

    def commit(self):
        print("TC run phase2 commit, tId=%s"%(self.current["transactionId"]))
        self.current["2pc"] = "commit"
        self.socket.sendto(encodeDict(self.current), self.cohort_addr)

    def abort(self):
        print("TC run phase2 abort, tId=%s"%(self.current["transactionId"]))
        self.current["2pc"] = "abort"
        self.socket.sendto(encodeDict(self.current), self.cohort_addr)

    # util
    def transactionId(self):
        old = self.counter
        self.counter += 1
        tId = self.hostId + str(old)
        return tId

    