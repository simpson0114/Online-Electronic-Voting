from concurrent import futures
from ctypes import resize
import logging
from random import choices
import signal
import sys
from typing import Optional

import grpc
import nacl
import eVoting_pb2
import eVoting_pb2_grpc

import secrets
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder
from datetime import datetime, timedelta
from DbAdapter import DbAdapter

# Define
TOKEN_SIZE = 4
CHALLENGE_SIZE = 4

class Server: 

    ''' Internal State '''
    # index: register_name, value: {"group", "public_key"}
    registration_table = {}
    # index: register_name, value: challenge
    challenge_table = {} 
    # index: token, value: {"expired", "name"}
    token_table = {} 
    # index: election_name, value: {"end_date", "groups", "votes", "voters"}
    election_table = {}

    ''' TOKEN '''

    def __init__(self, db_ip, db_port):
        self.db_ip = db_ip
        self.db_port = db_port

    def add_token(self, index, name):
        expired = datetime.now()+timedelta(hours=1)
        db = DbAdapter(self.db_ip, self.db_port)
        db.add_token(index, expired, name)
        #self.token_table[index] = {"expired": expired, "name": name}

    def isValid_token(self, index):
        #if index not in self.token_table:
        #    return False
        #expired = self.token_table[index]["expired"]
        db = DbAdapter(self.db_ip, self.db_port)
        expired, name = db.get_token(index)
        if name == None: # get_token() might return empty result
            return False
         else:
            return datetime.now()<expired

    def get_name_by_token(self, index):
        #return self.token_table[index]["name"]
        db = DbAdapter(self.db_ip, self.db_port)
        expired, name = db.get_token(index)
        return name

    ''' CHALLENGE '''

    def add_challenge(self, index, challenge):
        #self.challenge_table[index] = challenge
        db = DbAdapter(self.db_ip, self.db_port)
        db.add_challenge(index, challenge)

    def get_challenge(self, index):
        #return self.challenge_table[index]
        db = DbAdapter(self.db_ip, self.db_port)
        challenge = db.get_challenge(index)
        return challenge
    
    ''' REGISTRATION '''

    def add_register(self, index, group, public_key):
        db = DbAdapter(self.db_ip, self.db_port)
        status = db.add_register(index, group, public_key)
        return status
        #self.registration_table[index] = {"group": group, "public_key": public_key}

    def del_register(self, index):
        db = DbAdapter(self.db_ip, self.db_port)
        status = db.del_register(index)
        return status

    def get_register(self, index):
        db = DbAdapter(self.db_ip, self.db_port)
        group, public_key = db.get_register(index)
        table = {"group" : group, "public_key" : public_key}
        return table
        #return self.registration_table[index]

    def get_register_publicKey(self, index):
        db = DbAdapter(self.db_ip, self.db_port)
        group, public_key = db.get_register(index)
        return public_key
        #return self.registration_table[index]["public_key"]

    ''' ELECTION '''

    def add_election(self, election):
        db = DbAdapter(self.db_ip, self.db_port)
        index = election.name
        #votes = {}
        #for choice in election.choices:
        #    votes[choice] = 0
        due = election.end_date.ToDatetime()
        #self.election_table[index] = {"end_date": due, "groups": election.groups, "votes": votes, "voters": []}
        db.add_election(index, due, election.groups, election.choices)

    def isExisted_election(self, index):
        db = DbAdapter(self.db_ip, self.db_port)
        elections = db.get_all_elections()
        index = index.replace('?','')
        return index in elections
    
    def get_election(self, index):
        db = DbAdapter(self.db_ip, self.db_port)
        election = db.get_election(index)
        return election
        #return self.election_table[index]

    def add_vote(self, index, choice, voter):
        db = DbAdapter(self.db_ip, self.db_port)
        db.add_vote(index, choice, voter)
        #self.election_table[index]["votes"][choice] += 1
        #self.election_table[index]["voters"].append(voter)

    def isRepeated_vote(self, index, voter):
        election = self.get_election(index)
        return voter in election["voters"]

    def isValid_group(self, index, group):
        election = self.get_election(index)
        #election = self.election_table[index]
        group_list = election["groups"].split(',') ## group_list is infact a string not a list
        for iter in group_list:
            if iter == group:
                return True
        return False
         # return group in election["groups"]

    def isDue_election(self, index):
        election = self.get_election(index)
        #election = self.election_table[index]
        return datetime.now()>election["end_date"]

    def get_finalized_votes(self, index):
        election = self.get_election(index)
        #election = self.election_table[index]
        return election["votes"]

    ####################### Local Service API #######################
    def RegisterVoter(self, voter: eVoting_pb2.Voter) -> Optional[eVoting_pb2.Status]:
        try:
            index = voter.name
            public_key = VerifyKey(voter.public_key, encoder=Base64Encoder)
            status = self.add_register(index, voter.group, voter.public_key)
            return eVoting_pb2.Status(code=status)
            '''
            if index not in self.registration_table: 
                # Create a VerifyKey object from a hex serialized public key
                return eVoting_pb2.Status(code=0) # Status.code=0 : Successful registration
            else:
                return eVoting_pb2.Status(code=1) # Status.code=1 : Voter with the same name already exists
            '''

        except:
            return eVoting_pb2.Status(code=2) # Status.code=2 : Undefined error
        

    def UnregisterVoter(self, votername: eVoting_pb2.VoterName) -> Optional[eVoting_pb2.Status]:
        try:
            index = votername.name
            status = self.del_register(index)
            return eVoting_pb2.Status(code=status)
            '''
            if index in self.registration_table:  # Status.code=0 : Successful registration
                del self.registration_table[index]
                return eVoting_pb2.Status(code=0)
            else:
                return eVoting_pb2.Status(code=1) # Status.code=1 : No voter with the name exists on the server
            '''

        except:
            return eVoting_pb2.Status(code=2) # Status.code=2 : Undefined error



############################ RPC API ############################
class eVotingServicer(eVoting_pb2_grpc.eVotingServicer):

    def __init__(self, db_port):
        self.server = Server('localhost', db_port)  # handling internal state
        with open("public_key", "rb") as f:
            public_key_byte = f.read()
        self.server.RegisterVoter(eVoting_pb2.Voter(name="Frog", group="A", public_key=public_key_byte))

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
        self.server.add_challenge(key, challenge)
        return eVoting_pb2.Challenge(value = bytes(challenge))

    def Auth(self, request, context):
        authRequest = request
        index = authRequest.name.name
        public_key = self.server.get_register_publicKey(index)
        challenge = self.server.get_challenge(index)
        signature = authRequest.response.value
        try:
            public_key.verify(smessage=challenge, signature=signature) 
        except: # In case of invalid signature
            return eVoting_pb2.AuthToken(value = bytes("invalid", encoding="utf-8"))
        token = secrets.token_bytes(TOKEN_SIZE)
        self.server.add_token(token, index) # token is the index here
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

            self.server.add_election(election)

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
            
            self.server.add_vote(index, vote.choice_name, name)

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

def signal_handler(sig, frame):
    print('Server terminated.')
    sys.exit(0)

def serve(grpc_port, db_port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    eVoting_pb2_grpc.add_eVotingServicer_to_server(eVotingServicer(db_port), server)
    server.add_insecure_port('[::]:{}'.format(grpc_port))
    server.start()
    print("Server listening on port {}...".format(grpc_port))
    server.wait_for_termination()


if __name__ == '__main__':
    if len(sys.argv)!=3:
        print('need grpc server port and db server port')
        sys.exit()
    
    grpc_port = sys.argv[1]
    db_port = sys.argv[2]
    logging.basicConfig()
    signal.signal(signal.SIGINT, signal_handler)
    serve(grpc_port, db_port)
