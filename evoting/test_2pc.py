import base64
# from unittest import TestCase
import pytest
import grpc
from nacl.signing import SigningKey

import eVoting_pb2
import eVoting_pb2_grpc

from datetime import datetime, timedelta
from time import sleep
import server


class TestTemp:
    def test_preAuth_node_failure(self): # token == 2pc is down
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

            # Read private key from file
            with open("private_key", "rb") as f:
                serialized_key = f.read()

            serialized_key = base64.b64decode(serialized_key)
            singning_key = SigningKey(serialized_key)

            preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name="Bob"))
            
            assert preAuthResponse.value.decode("utf-8") == "2pc is down"

    def test_auth_node_failure(self):
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

            # Read private key from file
            with open("private_key", "rb") as f:
                serialized_key = f.read()

            serialized_key = base64.b64decode(serialized_key)
            singning_key = SigningKey(serialized_key)

            preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name="Bob"))

            challenge = preAuthResponse.value
            signed = singning_key.sign(challenge)
            signature = signed.signature

            authResponse = stub.Auth(eVoting_pb2.AuthRequest(
                name=eVoting_pb2.VoterName(name="Bob"), \
                response=eVoting_pb2.Response(value=bytes(signature)) \
                ))

            assert authResponse.value != b"2pc is down"

    def test_create_election_node_failure(self): # code == 1, error occur while preAuth, the error propagate
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

            # Read private key from file
            with open("private_key", "rb") as f:
                serialized_key = f.read()

            serialized_key = base64.b64decode(serialized_key)
            singning_key = SigningKey(serialized_key)

            preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name="Bob"))

            challenge = preAuthResponse.value
            signed = singning_key.sign(challenge)
            signature = signed.signature

            authResponse = stub.Auth(eVoting_pb2.AuthRequest(
                name=eVoting_pb2.VoterName(name="Bob"), \
                response=eVoting_pb2.Response(value=bytes(signature)) \
                ))

            token = authResponse.value

            # election config
            election_name = "Presidential"
            groups = ["A"]
            choices = ["A", "B", "C"]
            due = datetime.now() + timedelta(seconds=1)  # due 1 seconds later

            # call CreateElection (declare variable in a different way due to timestamp library)
            election = eVoting_pb2.Election()
            election.name = election_name
            election.groups.extend(groups)
            election.choices.extend(choices)
            election.end_date.FromDatetime(due)
            election.token.value = bytes(token)
            createElectionResponse = stub.CreateElection(election)

            assert str(createElectionResponse.code) == '1' 

    def test_cast_vote_success(self): # code == 1, error occur while preAuth, the error propagate
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

            # Read private key from file
            with open("private_key", "rb") as f:
                serialized_key = f.read()

            serialized_key = base64.b64decode(serialized_key)
            singning_key = SigningKey(serialized_key)

            preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name="Bob"))

            challenge = preAuthResponse.value
            signed = singning_key.sign(challenge)
            signature = signed.signature

            authResponse = stub.Auth(eVoting_pb2.AuthRequest(
                name=eVoting_pb2.VoterName(name="Bob"), \
                response=eVoting_pb2.Response(value=bytes(signature)) \
                ))

            token = authResponse.value

            # election config
            election_name = "Presidential"
            groups = ["A"]
            choices = ["A", "B", "C"]
            due = datetime.now() + timedelta(seconds=3)  # due 1 seconds later

            # call CreateElection (declare variable in a different way due to timestamp library)
            election = eVoting_pb2.Election()
            election.name = election_name
            election.groups.extend(groups)
            election.choices.extend(choices)
            election.end_date.FromDatetime(due)
            election.token.value = bytes(token)
            createElectionResponse = stub.CreateElection(election)

            # call CastVote
            castVoteResponse = stub.CastVote(eVoting_pb2.Vote(
                election_name=election_name,
                choice_name="A",
                token=eVoting_pb2.AuthToken(value=bytes(token))
            ))
            assert castVoteResponse.code == 1