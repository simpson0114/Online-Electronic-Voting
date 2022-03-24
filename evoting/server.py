from concurrent import futures
import logging
import signal
import sys
from typing import Optional

import grpc

import eVoting_pb2
import eVoting_pb2_grpc


####################### Local Service API #######################
def RegisterVoter(voter: eVoting_pb2.Voter) -> Optional[eVoting_pb2.Status]:
    pass

def UnregisterVoter(votername: eVoting_pb2.VoterName) -> Optional[eVoting_pb2.Status]:
    pass

#################################################################



############################ RPC API ############################
class eVotingServicer(eVoting_pb2_grpc.eVotingServicer):
    # Define every RPC call down below
    def PreAuth(self, request, context):
        print("Received PreAuth RPC call...")
        return eVoting_pb2.Challenge(value = bytes("123", encoding='utf8'))

    def Auth(self, request, context):
        print("Received Auth RPC call...")
        return eVoting_pb2.AuthToken(value = bytes("456", encoding='utf8'))

    def CreateElection(self, request, context):
        print("Received CreateElection RPC call...")
        return eVoting_pb2.Status(code = 789)

    def CastVote(self, request, context):
        print("Received CastVote RPC call...")
        return eVoting_pb2.Status(code = 101)

    def GetResult(self, request, context):
        print("Received GetResult RPC call...")

        result = eVoting_pb2.ElectionResult()
        result.status = 1

        theCount = result.counts.add()
        theCount.choice_name =  "Lincoln"
        theCount.count = 1000
        #theCount.token.value = bytes("SOS", encoding='utf8')
        return result

#################################################################

def signal_handler(sig, frame):
    print('Server terminated.')
    sys.exit(0)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    eVoting_pb2_grpc.add_eVotingServicer_to_server(eVotingServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server listening on port 50051...")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    signal.signal(signal.SIGINT, signal_handler)
    serve()
