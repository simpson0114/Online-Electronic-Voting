from __future__ import print_function

import logging

import grpc

import eVoting_pb2
import eVoting_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = eVoting_pb2_grpc.eVotingStub(channel)

        preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name = "Patrick"))
        
        authResponse = stub.Auth(eVoting_pb2.AuthRequest(
                    name = eVoting_pb2.VoterName(name = "Bob"),\
                    response = eVoting_pb2.Response(value = bytes("456", encoding='utf8'))\
                    ))

        election = eVoting_pb2.Election()
        election.name = "Alice"
        election.groups.extend("Team A")
        election.choices.extend("many choices")
        election.end_date.GetCurrentTime()
        election.token.value = bytes("789", encoding='utf8')
        createElectionResponse = stub.CreateElection(election)

        castVoteResponse = stub.CastVote(eVoting_pb2.Vote(\
                    election_name = "Congressional",\
                    choice_name = "Hamilton",\
                    token = eVoting_pb2.AuthToken(value = bytes("101", encoding='utf8'))\
        ))

        getResultResponse = stub.GetResult(eVoting_pb2.ElectionName(name = "Presidential"))


    print("Testing PreAuth... the Challenge is: " + preAuthResponse.value.decode("utf-8"))
    print("Testing Auth... the AuthToken is: " + authResponse.value.decode("utf-8"))
    print("Testing CreateElection... the ElectionStatus is: " + str(createElectionResponse.code))
    print("Testing CastVote... the VoteStatus is: " + str(castVoteResponse.code))
    print("Testing GetResult... the ElectionResult is: " + getResultResponse.count[0].choice_name)


if __name__ == '__main__':
    logging.basicConfig()
    run()
