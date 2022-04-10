# Online Electronic Voting – Part II. Single-Node e-Voting Server

## Design
We use Python to implement the voting server. 

PyNaCl, Python binding to the libsodium library, is used in the authentication process. After signing the challenge, client send back detached signature to RPC server. 
https://pynacl.readthedocs.io/en/latest/

With the unsure method to preserve internal state of the server, we encapsulate another class named Server to abstract the manipulation to data. Currently, the internal state is saved in memory with the data structure, dictiory. In the future, without modifying RPC server, it can be easily to preserve data in another way, for example, local files, database, etc. 



## Implementation

### RPC Server API
* __init__ 
    1. Server Object
    2. Toy Registration -> save private_key in local files, which read by client later
* PreAuth
* Auth
* CreateElection
* CastVote
* GetResult

### Server Internal Data
1. registration_table = {}
index: register_name, value: {"group", "public_key"}
2. challenge_table = {} 
index: register_name, value: challenge
3. token_table = {} 
index: token, value: {"expired", "name"}
4. election_table = {}
index: election_name, value: {"end_date", "groups", "votes", "voters"}

### Server API
1. registration
    * RegisterVoter
    * UnregisterVoter
    * add_register
    * get_register
    * get_register_publicKey
2. challenge
    * add_challenge
    * get_challenge
3. token
    * add_token
    * isValid_token
    * get_name_by_token
4. election
    * add_election
    * get_election
    * isExisted_election
    * add_vote
    * isRepeated_vote
    * isValid_group
    * isDue_election
    * get_finalized_votes

## Evaluation
Besides the reasonable operations, we also try the unreaonable operations trigger the detective functionalities, such as to get election result before due and vote repeatedly. And, all of them works. With Testing all kinds of functionalities, it is clear that the design and implementation works.

The screenshot down below shows that the server and the client run as expected. The terminal on the left is the server's logs of receiving RPC calls; the terminal on the right shows the responses that the client got from the server.

