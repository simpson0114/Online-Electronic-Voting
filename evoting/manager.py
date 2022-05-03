from concurrent import futures
from ctypes import resize
import logging
import signal
import sys

import grpc
import eVoting_pb2
import eVoting_pb2_grpc

from datetime import datetime, timedelta

PRIMARY_IP = 'localhost'
PRIMARY_PORT = 50002
BACKUP_IP = 'localhost'
BACKUP_PORT = 50003

class eVotingManager(eVoting_pb2_grpc.eVotingServicer):

    def __init__(self):
        self.primary = self.connect_server(PRIMARY_IP, PRIMARY_PORT)
        self.backup = self.connect_server(BACKUP_IP, BACKUP_PORT)
    
    def connect_server(self, ip, port):
        channel = grpc.insecure_channel('{ip}:{port}'.format(ip=ip,port=port))
        stub = eVoting_pb2_grpc.eVotingStub(channel)
        return stub

    def ft_grpc(self, p_callback, b_callback, request):
        try:
            res = p_callback(request, timeout=20.0)
        except: 
            res = b_callback(request, timeout=20.0)
        return res

    # Define every RPC call down below
    def PreAuth(self, request, context):
        return self.ft_grpc(self.primary.PreAuth, self.backup.PreAuth, request)

    def Auth(self, request, context):
        return self.ft_grpc(self.primary.Auth, self.backup.Auth, request)

    def CreateElection(self, request, context):
        return self.ft_grpc(self.primary.CreateElection, self.backup.CreateElection, request)

    def CastVote(self, request, context):
        return self.ft_grpc(self.primary.CastVote, self.backup.CastVote, request)

    def GetResult(self, request, context):
        return self.ft_grpc(self.primary.GetResult, self.backup.GetResult, request)




def signal_handler(sig, frame):
    print('Server terminated.')
    sys.exit(0)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    eVoting_pb2_grpc.add_eVotingServicer_to_server(eVotingManager(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server listening on port 50051...")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    signal.signal(signal.SIGINT, signal_handler)
    serve()