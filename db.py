import json
import sqlite3


class DBHelper:

    def __init__(self, dbname="vaccine_info.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup(self):
        tblstmt = "CREATE TABLE IF NOT EXISTS users (chat_id integer NOT NULL PRIMARY KEY, user_name text, user_state text, user_city text, user_pincode integer, user_location text, tg_user_id text, options text)"
        self.conn.execute(tblstmt)
        self.conn.commit()

    def add_user(self, chat_id, user_name, tg_user_id, options):
        stmt = "INSERT INTO users (chat_id, user_name, tg_user_id, options) VALUES (?, ?, ?, ?)"
        args = (chat_id, user_name, tg_user_id, options,)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_user(self, chat_id):
        stmt = "DELETE FROM users WHERE chat_id = (?)"
        args = (chat_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_all_chat_id(self):
        stmt = "SELECT chat_id FROM users"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_all_users(self):
        stmt = "SELECT chat_id, user_city, options FROM users"
        return [{'chat_id':x[0],'districts':x[1],'options':x[2]} for x in self.conn.execute(stmt)]
    
    def get_state_by_chat_id(self, chat_id):
        stmt = "SELECT user_state FROM users WHERE chat_id = (?)"
        args = (chat_id,)
        result = self.conn.execute(stmt, args).fetchall()
        return result[0][0]

    def get_districts_by_chat_id(self, chat_id):
        stmt = "SELECT user_city FROM users WHERE chat_id = (?)"
        args = (chat_id,)
        result = self.conn.execute(stmt, args).fetchall()
        try:
            return json.loads(result[0][0])
        except Exception:
            return []
    
    def get_preference_by_chat_id(self, chat_id):
        stmt = "SELECT options FROM users WHERE chat_id = (?)"
        args = (chat_id,)
        result = self.conn.execute(stmt, args).fetchall()
        try:
            return json.loads(result[0][0])
        except Exception:
            return {}

    def set_state_by_chat_id(self, state, chat_id):
        stmt = "UPDATE users SET user_state = (?) WHERE chat_id = (?)"
        args = (state, chat_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def set_city_by_chat_id(self, city, chat_id):
        stmt = "UPDATE users SET user_city = (?) WHERE chat_id = (?)"
        args = (city, chat_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def save_options_by_chat_id(self, options, chat_id):
        stmt = "UPDATE users SET options = (?) WHERE chat_id = (?)"
        args = (options, chat_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def check_user_by_chat_id(self, chat_id):
        stmt = "SELECT count(*) FROM users WHERE chat_id = (?)"
        args = (chat_id,)
        result = self.conn.execute(stmt, args).fetchall()
        return result[0][0]

    def get_all_chat_id_by_city(self, city):
        stmt = "SELECT chat_id FROM users WHERE user_city = (?)"
        args = (city,)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_admin_chat_id(self):
        stmt = "SELECT chat_id FROM users WHERE user_type = (?)"
        args = ("ADMIN",)
        result = self.conn.execute(stmt, args).fetchall()
        return result[0][0]
