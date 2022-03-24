# Online Electronic Voting – Part I. RPC Interface

## Design
We design a server-client framework based on the protocol given by the instructor. There will be a single server running on the localhost and the client can make a simple RPC call to the server via a specific port number.

## Implementation
In this homework we make all the RPC calls return dummy messages for the sake of concept validation which means the implantation of the functions are not done yet.

## Evaluation
Since we only need to make sure the RPC interfaces works, we hard-coded the client to make all the RPC calls once running.

The screenshot down below shows that the server and the client run as expected. The terminal on the left is the server's logs of receiving RPC calls; the terminal on the right shows the responses that the client got from the server.

![Imgur](https://i.imgur.com/ObLtLS7.png)