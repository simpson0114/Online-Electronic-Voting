python3 server.py -v 3000 -t 3001 -c 3002 -tp 4001 -cp 4002 &
python3 server.py -v 4000 -t 4001 -c 4002 -tp 3001 -cp 3002 &
python3 client.py
