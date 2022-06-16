from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder
from datetime import datetime, timedelta
from typing import Optional
import eVoting_pb2

from _2pc.tc import TC
from _2pc.cohort import Cohort
from DbAdapter import DbAdapter
class Server: 

    def __init__(self, TC_addr, cohort_addr, db_addr) -> None:
        
        ''' Internal State '''
        '''
        # index: register_name, value: {"group", "public_key"}
        self.registration_table = {}
        # index: register_name, value: challenge
        self.challenge_table = {} 
        # index: token, value: {"expired", "name"}
        self.token_table = {} 
        # index: election_name, value: {"end_date", "groups", "votes", "voters"}
        self.election_table = {}
        '''

        self.tc = TC(TC_addr, cohort_addr)
        self.db = DbAdapter(db_addr)

    ''' TOKEN '''

    def add_token(self, index, val, run2pc=False): #2pc
        if run2pc==True and self.tc.run(1, index, val)==False:
            return
        name = val["name"]
        expired = val["expired"]
        #self.token_table[index] = {"expired": expired, "name": name}
        self.db.add_token(index, expired, name)


    def isValid_token(self, index):
        #expired = self.token_table[index]["expired"]
        expired, name = self.db.get_token(index)
        return datetime.now()<expired

    def get_name_by_token(self, index):
        #return self.token_table[index]["name"]
        expired, name = self.db.get_token(index)
        return name

    ''' CHALLENGE '''

    def add_challenge(self, index, challenge, run2pc=False): #2pc
        if run2pc==True and self.tc.run(0, index, challenge)==False:
            return
        #self.challenge_table[index] = challenge
        print(challenge)
        self.db.add_challenge(index, challenge)

    def get_challenge(self, index):
        #return self.challenge_table[index]
        challenge = self.db.get_challenge(index)
        return challenge

    ''' REGISTRATION '''

    def add_register(self, index, val, run2pc=False): #2pc
        #self.registration_table[index] = {"group": group, "public_key": public_key}
        if run2pc==True and self.tc.run(4, index, val)==False:
            return
        group = val["group"]
        public_key = val["public_key"]
        status = self.db.add_register(index, group, public_key)
        return status

    def get_register(self, index):
        #return self.registration_table[index]
        group, public_key = self.db.get_register(index)
        table = {"group" : group, "public_key" : public_key}
        return table

    def get_register_publicKey(self, index):
        #return self.registration_table[index]["public_key"]
        group, public_key = self.db.get_register(index)
        return public_key

    ''' ELECTION '''

    def add_election(self, index, election, run2pc=False): #2pc election->grpc
        #index = election.name
        if run2pc==True and self.tc.run(2, index, election)==False:
            return
        #votes = {}
        #for choice in election.choices:
        #    votes[choice] = 0
        due = election.end_date.ToDatetime()
        #self.election_table[index] = {"end_date": due, "groups": election.groups, "votes": votes, "voters": []}
        self.db.add_election(index, due, election.groups, election.choices)
    
    def isExisted_election(self, index):
        #return index in self.election_table
        elections = self.db.get_all_elections()
        index = index.replace('?','')
        return index in elections

    def get_election(self, index):
        #return self.election_table[index]
        election = self.db.get_election(index)
        return election
    
    def add_vote(self, index, val, run2pc=False): #2pc
        if run2pc==True and self.tc.run(3, index, val)==False:
            return
        choice = val["choice"]
        voter = val["voter"]
        #self.election_table[index]["votes"][choice] += 1
        #self.election_table[index]["voters"].append(voter)
        self.db.add_vote(index, choice, voter)


    def isRepeated_vote(self, index, voter):
        #return voter in self.election_table[index]["voters"]
        election = self.get_election(index)
        return voter in election["voters"]

    def isValid_group(self, index, group):
        election = self.get_election(index)
        #election = self.election_table[index]
        return group in election["groups"]

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
            #public_key = VerifyKey(voter.public_key, encoder=Base64Encoder)
            
            val = {"group": voter.group, "public_key": voter.public_key}
            # Status.code=0 : Successful registration
            # Status.code=1 : Voter with the same name already exists
            res = self.add_register(index, val)
            return eVoting_pb2.Status(code=res) 

        except:
            return eVoting_pb2.Status(code=2) # Status.code=2 : Undefined error
        

    def UnregisterVoter(self, votername: eVoting_pb2.VoterName) -> Optional[eVoting_pb2.Status]:
        try:
            # Status.code=0 : Successful registration
            # Status.code=1 : No voter with the name exists on the server
            res = self.db.del_register(votername)
            return eVoting_pb2.Status(code=res)
            
        except:
            return eVoting_pb2.Status(code=2) # Status.code=2 : Undefined error
