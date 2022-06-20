from concurrent import futures
from ctypes import resize
import logging
from random import choices
import signal
import sys
from typing import Optional
from datetime import datetime, timedelta

import grpc
import nacl
import eVoting_pb2
import eVoting_pb2_grpc
from internal_server import Server
import secrets
from _2pc.tc import TC
from _2pc.cohort import Cohort
import threading

import argparse

#Define
TOKEN_SIZE = 4
CHALLENGE_SIZE = 4

IP = '127.0.0.1'

############################ RPC API ############################
class eVotingServicer(eVoting_pb2_grpc.eVotingServicer):

    def __init__(self, TC_addr, cohort_addr, db_addr):
        self.server = Server(TC_addr, cohort_addr, db_addr)  # handling internal state 
        '''toy registration'''
        
        with open("public_key", "rb") as f:
            public_key_byte = f.read()
        self.UnregisterVoter("Bob")
        self.RegisterVoter(eVoting_pb2.Voter(name="Bob", group="A", public_key=public_key_byte))


    def RegisterVoter(self, voter: eVoting_pb2.Voter):
        self.server.RegisterVoter(voter)
    
    def UnregisterVoter(self, votername: eVoting_pb2.VoterName):
        self.server.UnregisterVoter(votername)

    # Define every RPC call down below
    def PreAuth(self, request, context):
        print("Received PreAuth RPC call...")
        voterName = request
        key = voterName.name
        challenge = secrets.token_bytes(CHALLENGE_SIZE)
        try:
            self.server.add_challenge(key, challenge, run2pc=True)
        except:
            return eVoting_pb2.Challenge(value = bytes("2pc is down", encoding="utf-8"))
        return eVoting_pb2.Challenge(value = bytes(challenge))
    
    def Auth(self, request, context):
        authRequest = request
        index = authRequest.name.name
        challenge = self.server.get_challenge(index)
        public_key = self.server.get_register_publicKey(index)
        signature = authRequest.response.value
        try:
            public_key.verify(smessage=challenge, signature=signature) 
        except: # In case of invalid signature
            return eVoting_pb2.AuthToken(value = bytes("invalid", encoding="utf-8"))
        token = secrets.token_bytes(TOKEN_SIZE)
        expired = datetime.now()+timedelta(hours=1)
        val = {"name": index, "expired": expired}
        try:
            self.server.add_token(token, val, run2pc=True) # token is the index here
        except:
            return eVoting_pb2.AuthToken(value = bytes("2pc is down", encoding="utf-8"))
        return eVoting_pb2.AuthToken(value = bytes(token))

    def CreateElection(self, request, context):
        print("Received CreateElection RPC call...")
        election = request
        token = election.token.value
        try:
            if not self.server.isValid_token(token):
                return eVoting_pb2.Status(code = 1) # Status.code=1 : Invalid authentication token

            if len(election.choices)==0 or len(election.groups)==0:
                return eVoting_pb2.Status(code = 2) # Status.code=2 : Missing groups or choices specification (at least one group and one choice should be listed for the election)

            self.server.add_election(election.name, election, run2pc=True)

            return eVoting_pb2.Status(code = 0) # Status.code=0 : Election created successfully
        except:
            return eVoting_pb2.Status(code = 3) # Status.code=3 : Unknown error

    def CastVote(self, request, context):
        print("Received CastVote RPC call...")
        vote = request
        index = vote.election_name
        token = vote.token.value
        try:
            if not self.server.isValid_token(token):
                return eVoting_pb2.Status(code = 1) # Status.code=1 : Invalid authentication token

            
            if not self.server.isExisted_election(index) or self.server.isDue_election(index):
                return eVoting_pb2.Status(code = 2) # Status.code=2 : Invalid election name
            
            name = self.server.get_name_by_token(token)
            register = self.server.get_register(name)
            group = register["group"]

            if not self.server.isValid_group(index, group):
                return eVoting_pb2.Status(code = 3) # Status.code=3 : The voter’s group is not allowed in the election
            
            if self.server.isRepeated_vote(index, name):
                return eVoting_pb2.Status(code = 4) # Status.code=4 : A previous vote has been cast.
            
            val = {"choice": vote.choice_name, "voter": name}
            self.server.add_vote(index, val, run2pc=True)

            return eVoting_pb2.Status(code = 0) # Status.code=0 : Successful vote
        except:
            return eVoting_pb2.Status(code = 5) # Status.code=5 : Unknown error.

    def GetResult(self, request, context):
        print("Received GetResult RPC call...")
        electionName = request
        index = electionName.name

        result = eVoting_pb2.ElectionResult()
        

        if not self.server.isExisted_election(index):
            result.status = 1
            return result # ElectionResult.status = 1: Non-existent election
        if not self.server.isDue_election(index):
            result.status = 2
            return result # ElectionResult.status = 2: The election is still ongoing. Election result is not available yet.

        result = eVoting_pb2.ElectionResult()
        result.status = 0
        votes = self.server.get_finalized_votes(index) 
        for choice, ballots in votes.items():
            theCount = result.counts.add()
            theCount.choice_name = choice
            theCount.count = ballots

        return result # ElectionReuslt.status = 0
    

#################################################################

#################################################################


def run_cohort(cohort):
    cohort.wait()

def signal_handler(sig, frame):
    print('Server terminated.')
    sys.exit(0)

def serve(args):

    vport = args.vport
    tcport = args.tcport
    coport = args.coport
    tcport_partner = args.tcport_partner
    coport_partner = args.coport_partner
    db_port = args.database_port

    TC_addr = (IP, tcport)
    cohort_partner_addr = (IP, coport_partner)
    cohort_addr = (IP, coport)
    TC_partner_addr = (IP, tcport_partner)
    db_addr = (IP, db_port)

    eVotingServer = eVotingServicer(TC_addr, cohort_partner_addr, db_addr)

    # Cohort
    cohort = Cohort(cohort_addr, TC_partner_addr, eVotingServer.server)
    t = threading.Thread(target=run_cohort, args=(cohort, ))
    t.start()


    # Server & TC
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    eVoting_pb2_grpc.add_eVotingServicer_to_server(eVotingServer, server)
    server.add_insecure_port('[::]:{}'.format(vport))
    server.start()
    print("Server listening on port {}...".format(vport))
    server.wait_for_termination()



if __name__ == '__main__':
  
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vport', type=int)
    parser.add_argument('-t', '--tcport', type=int)
    parser.add_argument('-c', '--coport', type=int)
    parser.add_argument('-tp', '--tcport_partner', type=int) # to connect
    parser.add_argument('-cp', '--coport_partner', type=int) # to connect
    parser.add_argument('-db', '--database_port', type=int)
    args = parser.parse_args()

    logging.basicConfig()
    signal.signal(signal.SIGINT, signal_handler)
    serve(args)
