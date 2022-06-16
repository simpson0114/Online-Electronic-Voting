curl -L https://github.com/rqlite/rqlite/releases/download/v7.5.1/rqlite-v7.5.1-linux-amd64.tar.gz -o rqlite-v7.5.1-linux-amd64.tar.gz
tar xvfz rqlite-v7.5.1-linux-amd64.tar.gz

git clone https://github.com/rqlite/pyrqlite.git
cd pyrqlite
sudo python3 setup.py install
cd ..