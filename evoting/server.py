from concurrent import futures
import logging

import grpc
# import helloworld_pb2
# import helloworld_pb2_grpc

import eVoting_pb2
import eVoting_pb2_grpc

# class Greeter(helloworld_pb2_grpc.GreeterServicer):

#     def SayHello(self, request, context):
#         return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)

class eVotingServicer(eVoting_pb2_grpc.eVotingServicer):

    def PreAuth(self, request, context):
        return eVoting_pb2.Challenge(value = b'\x00')

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    #helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    eVoting_pb2_grpc.add_eVotingServicer_to_server(eVotingServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server listening on port 50051...")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
