import sqlite3
import os
from datetime import datetime

TOKEN_SIZE = 4
CHALLENGE_SIZE = 4

class DbAdapter:
    def __init__(self):
        self.database = 'evoting.db'

        conn = sqlite3.connect(self.database)
        conn.execute("CREATE TABLE IF NOT EXISTS Registration(name text NOT NULL, \
                                                 groups text NOT NULL, \
                                                 public_key text NOT NULL)")

        conn.execute("CREATE TABLE IF NOT EXISTS Challenge(name text NOT NULL, \
                                                           challenge text NOT NULL)")

        conn.execute("CREATE TABLE IF NOT EXISTS Token(token text NOT NULL, \
                                                       expired text NOT NULL, \
                                                       name text NOT NULL)")

        conn.execute("CREATE TABLE IF NOT EXISTS Election(election_name text NOT NULL, \
                                                          end_date text NOT NULL, \
                                                          groups text NOT NULL, \
                                                          voters text NOT NULL)")
        conn.commit()
        conn.close()

    def add_register(self, name, group, public_key):
        conn = sqlite3.connect(self.database)
        data = conn.execute(f"SELECT groups,public_key from Registration WHERE name='{name}'").fetchone()
        if data is not None:
            status =  1  # Status.code=1 : Voter with the same name already exists
        else:
            key = int.from_bytes(public_key, byteorder='big', signed=False)
            conn.execute(f"INSERT INTO Registration values('{name}','{group}','{key}')")
            status =  0  # Status.code=0 : Successful registration
        conn.commit()
        conn.close()

        return status

    def del_register(self, name):
        conn = sqlite3.connect(self.database)
        data = conn.execute(f"SELECT groups,public_key from Registration WHERE name='{name}'").fetchone()
        if data is None:
            status =  1  # Status.code=1 : No voter with the name exists on the server
        else:
            conn.execute(f"DELETE from Registration WHERE name='{name}'")
            status =  0  # Status.code=0 : Successful unregistration
        conn.commit()
        conn.close()

        return status

    def get_register(self, name):
        conn = sqlite3.connect(self.database)
        data = conn.execute(f"SELECT groups,public_key from Registration WHERE name='{name}'").fetchone()
        conn.commit()
        conn.close()

        if data is None:
            return None, None
        else:
            group = data[0]
            public_key = int(data[1]).to_bytes(32, byteorder="big")
            return group, public_key

    def add_challenge(self, name, challenge):
        conn = sqlite3.connect(self.database)
        conn.execute(f"DELETE from Challenge WHERE name='{name}'")
        challenge_toint = int.from_bytes(challenge, byteorder='big', signed=False)
        conn.execute(f"INSERT INTO Challenge values('{name}','{challenge_toint}')")
        conn.commit()
        conn.close()

    def get_challenge(self, name):
        conn = sqlite3.connect(self.database)
        data = conn.execute(f"SELECT challenge from Challenge WHERE name='{name}'").fetchone()
        conn.commit()
        conn.close()

        if data is None:
            return None
        else:
            challenge = int(data[0]).to_bytes(CHALLENGE_SIZE, byteorder="big")
            return challenge

    def add_token(self, token, expired, name):
        conn = sqlite3.connect(self.database)
        token_toint = int.from_bytes(token, byteorder='big', signed=False)
        expired_time = expired.strftime("%m/%d/%Y, %H:%M:%S")
        conn.execute(f"DELETE from Token WHERE token='{token_toint}'")
        conn.execute(f"INSERT INTO Token values('{token_toint}','{expired_time}','{name}')")
        conn.commit()
        conn.close()

    def get_token(self, token):
        conn = sqlite3.connect(self.database)
        token_toint = int.from_bytes(token, byteorder='big', signed=False)
        datas = conn.execute(f"SELECT expired,name from Token WHERE token='{token_toint}'").fetchone()
        conn.commit()
        conn.close()

        if datas is None:
            return None, None
        else:
            expired_time = datetime.strptime(datas[0], "%m/%d/%Y, %H:%M:%S")
            name = datas[1]
            return expired_time, name

    def add_election(self, election_name, end_date, groups, choices):
        conn = sqlite3.connect(self.database)
        end_date_tostr = end_date.strftime("%m/%d/%Y, %H:%M:%S")
        groups_tostr = ','.join(groups)
        voters = ''
        conn.execute(f"DELETE from Election WHERE election_name='{election_name}'")
        conn.execute(f"INSERT INTO Election values('{election_name}','{end_date_tostr}', \
                                                    '{groups_tostr}','{voters}')")
        conn.execute(f"DROP TABLE IF EXISTS {election_name}")                                            
        conn.execute(f"CREATE TABLE {election_name}(name text NOT NULL, \
                                                    votes integer NOT NULL)")
        
        choices_list = []
        if type(choices) is str:
            for chioce in choices.split(','):
                choices_list.append(choice)
        elif type(choices) is list:
            choices_list = choices
            
        for choice in choices_list:
            conn.execute(f"INSERT INTO {election_name} values('{choice}',0)")

        conn.commit()
        conn.close()

    def get_all_elections(self):
        conn = sqlite3.connect(self.database)
        datas = conn.execute(f"SELECT election_name from Election").fetchall()

        elections = []
        for data in datas:
            elections.append(data[0])
        return elections

    def get_election(self, election_name):
        conn = sqlite3.connect(self.database)
        datas = conn.execute(f"SELECT end_date,groups,voters from Election WHERE election_name='{election_name}'").fetchone()
        end_date = datetime.strptime(datas[0], "%m/%d/%Y, %H:%M:%S")
        groups = datas[1]
        voters = datas[2]

        datas = conn.execute(f"SELECT name,votes from {election_name}").fetchall()
        votes = {}
        for data in datas:
            votes[data[0]] = data[1]

        table = {'end_date':end_date, 'groups':groups, 'votes':votes, 'voters':voters}
        return table

    def add_vote(self, election_name, choice, voter):
        conn = sqlite3.connect(self.database)
        voters = conn.execute(f"SELECT voters from Election WHERE election_name='{election_name}'").fetchone()
        if voters is None:
            print(f'There no election name {election_name}')
            conn.commit()
            conn.close()
            return
        votes = conn.execute(f"SELECT votes from {election_name} WHERE name='{choice}'").fetchone()
        if votes is None:
            print(f'There no candidate name {choice}')
            conn.commit()
            conn.close()
            return

        if voters[0] == '':
            voters = voter
        else:
            voters = voters[0] + f',{voter}'
        sql = ''' UPDATE Election
              SET voters = ?
              WHERE election_name = ?'''
        cur = conn.cursor()
        cur.execute(sql, (voters, election_name))

        votes = votes[0] + 1
        sql = f''' UPDATE {election_name}
              SET votes = ?
              WHERE name = ?'''
        cur.execute(sql, (votes, choice))

        conn.commit()
        conn.close()