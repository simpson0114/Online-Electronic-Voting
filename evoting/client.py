from __future__ import print_function

import logging
from time import sleep

import grpc
from numpy import sign

import eVoting_pb2
import eVoting_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from nacl.signing import SigningKey
from datetime import datetime, timedelta



def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        # create a stub for RPC call
        stub = eVoting_pb2_grpc.eVotingStub(channel)

        # Read private key from file
        with open("private_key", "rb") as f:
            serialized_key = f.read()

        singning_key = SigningKey(serialized_key)

        # call PreAuth
        preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name = "Bob"))
        
        # call Auth
        challenge = preAuthResponse.value
        signed = singning_key.sign(challenge)
        signature = signed.signature
        
        authResponse = stub.Auth(eVoting_pb2.AuthRequest(
                    name = eVoting_pb2.VoterName(name = "Bob"),\
                    response = eVoting_pb2.Response(value = bytes(signature))\
        ))

        token = authResponse.value

        
        # election config
        election_name = "Where is the Swaggest place for having sex?"
        groups = ["Team A", "Team B"]
        choices = ["Highway", "Resturant", "sense Lab"]
        due = datetime.now()+timedelta(seconds=1) # due 1 seconds later

        # call CreateElection (declare variable in a different way due to timestamp library)
        election = eVoting_pb2.Election()
        election.name = election_name
        election.groups.extend(groups)
        election.choices.extend(choices)
        election.end_date.FromDatetime(due) 
        election.token.value = bytes(token)
        createElectionResponse = stub.CreateElection(election)

        #call CastVote
        castVoteResponse = stub.CastVote(eVoting_pb2.Vote(\
                    election_name = election_name,\
                    choice_name = "sense Lab",\
                    token = eVoting_pb2.AuthToken(value = bytes(token))\
        ))

        # call GetResult
        getResultResponse = stub.GetResult(eVoting_pb2.ElectionName(name=election_name))
        print("Testing GetResult Before Due... the Status is: "+ str(getResultResponse.status))
        print("----")

        sleep(1)

        # call GetResult
        getResultResponse = stub.GetResult(eVoting_pb2.ElectionName(name=election_name))

        # print the responses of the RPC calls above
        print("Testing PreAuth... the Challenge is: ")
        print(preAuthResponse.value)
        print("Testing Auth... the AuthToken is: ")
        print(authResponse.value)
        print("Testing CreateElection... the Status is: " + str(createElectionResponse.code))
        print("Testing CastVote... the Status is: " + str(castVoteResponse.code))
        print("Testing GetResult... the Status is: " + str(getResultResponse.status))
        for voteCount in getResultResponse.counts:
            print("Choice {} got {} ballots in election!".format(voteCount.choice_name, voteCount.count))

        # overdue vote
        castVoteResponse = stub.CastVote(eVoting_pb2.Vote(\
                        election_name = election_name,\
                        choice_name = "sense Lab",\
                        token = eVoting_pb2.AuthToken(value = bytes(token))\
        ))
        print("----")
        print("Testing CastVote Overdue... the Status is: " + str(castVoteResponse.code))


if __name__ == '__main__':
    logging.basicConfig()
    run()
