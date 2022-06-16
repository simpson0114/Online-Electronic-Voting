#import pymysql as dbapi2
import pyrqlite.dbapi2 as dbapi2
from math import log
import os
from datetime import datetime
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder

TOKEN_SIZE = 4
CHALLENGE_SIZE = 4


class DbAdapter:
    def __init__(self, db_addr):
        db_settings = {"host": db_addr[0], "port": db_addr[1]}
        self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS Registration(name text NOT NULL, \
                                                                    groups text NOT NULL, \
                                                                    public_key text NOT NULL)")

            cursor.execute("CREATE TABLE IF NOT EXISTS Challenge(name text NOT NULL, \
                                                                challenge text NOT NULL)")

            cursor.execute("CREATE TABLE IF NOT EXISTS Token(token text NOT NULL, \
                                                             expired text NOT NULL, \
                                                             name text NOT NULL)")

            cursor.execute("CREATE TABLE IF NOT EXISTS Election(election_name text NOT NULL, \
                                                                end_date text NOT NULL, \
                                                                groups text NOT NULL, \
                                                                voters text NOT NULL)")
        self.conn.commit()
        #self.conn.close()

    def add_register(self, name, group, public_key):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT `groups`,public_key from Registration WHERE name='{name}'")
            data = cursor.fetchone()
            if data is not None:
                status =  1  # Status.code=1 : Voter with the same name already exists
            else:
                key = int.from_bytes(public_key, byteorder='big', signed=False)
                #print(key)
                #key = public_key.hex()
                cursor.execute(f"INSERT INTO `Registration` values('{name}','{group}','{key}')")
                status =  0  # Status.code=0 : Successful registration
        self.conn.commit()
        #self.conn.close()

        return status

    def del_register(self, name):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT `groups`,public_key from Registration WHERE name='{name}'")
            data = cursor.fetchone()
            if data is None:
                status =  1  # Status.code=1 : No voter with the name exists on the server
            else:
                cursor.execute(f"DELETE from Registration WHERE name='{name}'")
                status =  0  # Status.code=0 : Successful unregistration
        self.conn.commit()
        #self.conn.close()

        return status

    def bytes_needed(self, n):
        if n == 0:
            return 1
        return int(log(n, 256)) + 1

    def get_register(self, name):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT `groups`,public_key from Registration WHERE name='{name}'")
            data = cursor.fetchone()
        #self.conn.close()

        if data is None:
            return None, None
        else:
            group = data[0]
            bytes_need = self.bytes_needed(int(data[1]))
            public_key = int(data[1]).to_bytes(bytes_need, byteorder="big")
            #missing_padding = 4 - len(public_key) % 4
            #if missing_padding:
            #    public_key += b'=' * missing_padding
            public_key = VerifyKey(public_key, encoder=Base64Encoder)
            return group, public_key

    def add_challenge(self, name, challenge):
        #self.conn = dbapi2.connect(**self.db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute(f"DELETE from Challenge WHERE name='{name}'")
            challenge_toint = int.from_bytes(challenge, byteorder='big', signed=False)
            cursor.execute(f"INSERT INTO `Challenge` values('{name}','{challenge_toint}')")
        self.conn.commit()
        #self.conn.close()

    def get_challenge(self, name):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT challenge from Challenge WHERE name='{name}'")
            data = cursor.fetchone()
        #self.conn.close()

        if data is None:
            return None
        else:
            challenge = int(data[0]).to_bytes(CHALLENGE_SIZE, byteorder="big")
            return challenge

    def add_token(self, token, expired, name):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            token_toint = int.from_bytes(token, byteorder='big', signed=False)
            expired_time = expired.strftime("%m/%d/%Y, %H:%M:%S")
            cursor.execute(f"DELETE from Token WHERE token='{token_toint}'")
            cursor.execute(f"INSERT INTO `Token` values('{token_toint}','{expired_time}','{name}')")
        self.conn.commit()
        #self.conn.close()

    def get_token(self, token):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            token_toint = int.from_bytes(token, byteorder='big', signed=False)
            cursor.execute(f"SELECT expired,name from Token WHERE token='{token_toint}'")
            datas = cursor.fetchone()
        #self.conn.close()

        if datas is None:
            return None, None
        else:
            expired_time = datetime.strptime(datas[0], "%m/%d/%Y, %H:%M:%S")
            name = datas[1]
            return expired_time, name

    def add_election(self, election_name, end_date, groups, choices):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            election_name = election_name.replace('?', '')
            end_date_tostr = end_date.strftime("%m/%d/%Y, %H:%M:%S")
            groups_tostr = ','.join(groups)
            voters = ''
            cursor.execute(f"DELETE from Election WHERE election_name='{election_name}'")
            cursor.execute(f"INSERT INTO `Election` values('{election_name}','{end_date_tostr}', \
                                                        '{groups_tostr}','{voters}')")
            cursor.execute(f"DROP TABLE IF EXISTS '{election_name}'")                                            
            cursor.execute(f"CREATE TABLE '{election_name}'(`name` text NOT NULL, \
                                                            `votes` integer NOT NULL)")
            
            
                
            for choice in choices:
                print(choice)
                cursor.execute(f"INSERT INTO `{election_name}` values('{choice}',0)")

        self.conn.commit()
        #self.conn.close()

    def get_all_elections(self):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT election_name from Election")
            datas = cursor.fetchall()
        #self.conn.close()

        elections = []
        for data in datas:
            elections.append(data[0])
        return elections

    def get_election(self, election_name):
        #self.conn = dbapi2.connect(**db_settings)
        with self.conn.cursor() as cursor:
            election_name = election_name.replace('?', '')
            cursor.execute(f"SELECT end_date,`groups`,voters from Election WHERE election_name='{election_name}'")
            datas = cursor.fetchone()

            end_date = datetime.strptime(datas[0], "%m/%d/%Y, %H:%M:%S")
            groups = datas[1]
            voters = datas[2]

            cursor.execute(f"SELECT name,votes from '{election_name}'")
            datas = cursor.fetchall()
            votes = {}
            for data in datas:
                votes[data[0]] = data[1]
        #self.conn.close()

        table = {'end_date':end_date, 'groups':groups, 'votes':votes, 'voters':voters}
        return table

    def add_vote(self, election_name, choice, voter):
        print("cast vote to %s..."%(election_name))
        election_name = election_name.replace('?', '')
        #self.conn = dbapi2.connect(**db_settings)
        print(election_name)
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT voters from Election WHERE election_name='{election_name}'")
            voters = cursor.fetchone()
            if voters is None:
                print(f'There no election name {election_name}')
                self.conn.commit()
                #self.conn.close()
                return
            cursor.execute(f"SELECT votes from '{election_name}' WHERE name='{choice}'")
            votes = cursor.fetchone()
            if votes is None:
                print(f'There no candidate name {choice}')
                self.conn.commit()
                #self.conn.close()
                return

            if voters[0] == '':
                voters = voter
            else:
                voters = voters[0] + f',{voter}'
            sql = f"UPDATE Election SET voters = '{voters}' WHERE election_name = '{election_name}'"
            cursor.execute(sql)

            votes = votes[0] + 1
            sql = f" UPDATE '{election_name}' SET votes = '{votes}' WHERE name = '{choice}'"
            cursor.execute(sql)

        self.conn.commit()
        #self.conn.close()