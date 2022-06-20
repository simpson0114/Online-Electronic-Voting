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

class TesteVotingServicer:

    def test_pre_auth(self):
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)
            preAuthResponse = stub.PreAuth(eVoting_pb2.VoterName(name="Bob"))
            assert preAuthResponse != ""

    def test_auth_valid(self):
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
            assert authResponse.value != b"invalid"

    def test_auth_invalid(self):
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

            authResponse = stub.Auth(eVoting_pb2.AuthRequest(
                name=eVoting_pb2.VoterName(name="Bob"), \
                response=eVoting_pb2.Response(value=bytes("wrong signature",  encoding="utf-8")) \
                ))
            assert authResponse.value == b"invalid"

    def test_create_election_success(self): # code == 0
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

            assert str(createElectionResponse.code) == '0' # create successfully

    def test_create_election_invalid_auth_token(self): # code == 1
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

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
            election.token.value = bytes("Wrong token", encoding = "utf-8")
            createElectionResponse = stub.CreateElection(election)

            assert str(createElectionResponse.code) == '1' # Invalid authentication token

    def test_create_election_missing_parameter(self): # code == 2
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
            #choices = ["A", "B", "C"]
            due = datetime.now() + timedelta(seconds=5)  # due 1 seconds later

            # call CreateElection (declare variable in a different way due to timestamp library)
            election = eVoting_pb2.Election()
            election.name = election_name
            election.groups.extend(groups)
            #election.choices.extend(choices)
            election.end_date.FromDatetime(due)
            election.token.value = bytes(token)
            createElectionResponse = stub.CreateElection(election)

            assert str(createElectionResponse.code) == '2' # missing parameters

    def test_cast_vote_success(self): # code == 0
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
            assert castVoteResponse.code == 0

    def test_cast_vote_invalid_auth_token(self): #error code 1
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
                token=eVoting_pb2.AuthToken(value=bytes("Wrong token", encoding="utf-8"))
            ))
            assert castVoteResponse.code == 1 # Invalid authentication token

    def test_cast_vote_invalid_election_name(self): #code == 2
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

            # call CastVote
            castVoteResponse = stub.CastVote(eVoting_pb2.Vote(
                election_name="invalid name",
                choice_name="A",
                token=eVoting_pb2.AuthToken(value=bytes(token))
            ))
            assert castVoteResponse.code == 2

    def test_cast_vote_wrong_voter_group(self): # code == 3
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
            election_name = "Presidential_wrong_group"
            groups = ["Not for A"]
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
            assert castVoteResponse.code == 3 # The voter’s group is not allowed in the election

    def test_cast_vote_already_voted(self): # code == 4
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
            due = datetime.now() + timedelta(seconds=5)  # due 1 seconds later

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
            castVoteResponse = stub.CastVote(eVoting_pb2.Vote(
                election_name=election_name,
                choice_name="A",
                token=eVoting_pb2.AuthToken(value=bytes(token))
            ))
            assert castVoteResponse.code == 4 #  A previous vote has been cast.

    def test_get_result_success(self):
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

            # call CastVote
            castVoteResponse = stub.CastVote(eVoting_pb2.Vote(
                election_name=election_name,
                choice_name="A",
                token=eVoting_pb2.AuthToken(value=bytes(token))
            ))

            sleep(2)

            # call GetResult
            getResultResponse = stub.GetResult(eVoting_pb2.ElectionName(name=election_name))
            assert getResultResponse.status == 0

            for voteCount in getResultResponse.counts:
                if voteCount.choice_name == 'A':
                    assert voteCount.count == 1
                elif voteCount.choice_name == 'B':
                    assert voteCount.count == 0
                elif voteCount.choice_name == 'C':
                    assert voteCount.count == 0

    def test_get_result_non_existent_election(self):
        with grpc.insecure_channel('localhost:3100') as channel:
            # create a stub for RPC call
            stub = eVoting_pb2_grpc.eVotingStub(channel)

            # call GetResult
            getResultResponse = stub.GetResult(eVoting_pb2.ElectionName(name="Non-existent election"))
            assert getResultResponse.status == 1 # Non-existent election

    def test_get_result_election_not_due(self): # status == 2
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
            due = datetime.now() + timedelta(seconds=5)  # due 1 seconds later

            # call CreateElection (declare variable in a different way due to timestamp library)
            election = eVoting_pb2.Election()
            election.name = election_name
            election.groups.extend(groups)
            election.choices.extend(choices)
            election.end_date.FromDatetime(due)
            election.token.value = bytes(token)
            createElectionResponse = stub.CreateElection(election)

            # call GetResult
            getResultResponse = stub.GetResult(eVoting_pb2.ElectionName(name=election_name))
            assert getResultResponse.status == 2

