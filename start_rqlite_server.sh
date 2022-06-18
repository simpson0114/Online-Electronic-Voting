cd rqlite-v7.5.1-linux-amd64
./rqlited -http-addr localhost:4001 -raft-addr localhost:4002 ~/node.1 &
./rqlited -http-addr localhost:4003 -raft-addr localhost:4004 ~/node.2