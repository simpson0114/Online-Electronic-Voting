

import socket
from _2pc.util import encodeDict, decodeDict

MAX_PACKET_SIZE = 1024

class Cohort:
    def __init__(self, cohort_addr, tc_addr, server):
        self.tc_addr = tc_addr
        self.counter = 0
        self.hostId = str(cohort_addr)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(cohort_addr)
        self.server = server
        self.current = {}
        print("Cohort listening on port {}...".format(cohort_addr[1]))


    def wait(self):
        self.socket.settimeout(None)
        recv_raw = self.socket.recv(MAX_PACKET_SIZE)
        #print(recv_raw)
        self.current = decodeDict(recv_raw)
        self.respond()

    def respond(self):
        print("Cohort run phase1 respond, tId=%s"%(self.current["transactionId"]))
        # no check needed
        res = "yes"
        self.current["2pc"] = res
        self.socket.sendto(encodeDict(self.current), self.tc_addr)
        self.final()

    def final(self):
        self.socket.settimeout(5)
        try:
            recv_raw = self.socket.recv(MAX_PACKET_SIZE)
            recv = decodeDict(recv_raw)
        except: # timeout
            self.abort()

        recv_transactionId = recv["transactionId"]
        final = recv["2pc"]
        if self.current["transactionId"]==recv_transactionId and final=="commit":
            self.commit()
        else:
            self.abort()
        self.wait()


    def commit(self):
        print("Cohort run phase2 commit, tId=%s"%(self.current["transactionId"]))
        actionId = self.current["actionId"]
        arg_key = self.current["arg_key"]
        arg_val = self.current["arg_val"]

        if actionId==0:
            self.server.add_challenge(arg_key, arg_val)
        elif actionId==1:
            self.server.add_token(arg_key, arg_val)
        elif actionId==2:
            self.server.add_election(arg_key, arg_val)
        elif actionId==3:
            self.server.add_vote(arg_key, arg_val)
        elif actionId==4:
            self.server.add_register(arg_key, arg_val)


    def abort(self):
        print("Cohort run phase2 abort, tId=%s"%(self.current["transactionId"]))

