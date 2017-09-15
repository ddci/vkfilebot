import logging

__author__ = 'Daniil Nikulin'
__copyright__ = "Copyright 2017,VK File Bot"
__license__ = "Apache License 2.0"
__version__ = "1.0"
__maintainer__ = "Daniil Nikulin"
__email__ = "danil.nikulin@gmail.com"
__status__ = "Production"
import os
import datetime
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    chat_id = db.Column(db.BigInteger, unique=True)
    search_req_last = db.Column(db.String(200))
    user_step = db.Column(db.Integer)
    joined_on_utc = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __init__(self, first_name, last_name, cid, lastq, userstep):
        self.first_name = first_name
        self.last_name = last_name
        self.chat_id = cid
        self.search_req_last = lastq
        self.user_step = userstep


class Requests(db.Model):
    __tablename__ = "requests"
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger, db.ForeignKey('data.chat_id'), nullable=False)
    search_request = db.Column(db.String(200))
    file_type = db.Column(db.Integer)
    submitted_on_utc = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __init__(self, cid, search_req, file_type):
        self.chat_id = cid
        self.search_request = search_req
        self.file_type = file_type


def add_request_to_db(cid, req, file_type):
    try:
        request = Requests(int(cid), str(req), int(file_type))
        db.session.add(request)
        db.session.commit()
    except Exception as e:
        logging.exception("Error in add_request_to_db error = %s", e)


def set_user_step_to_db(cid, step):
    try:
        if is_user_exist(cid):
            user = db.session.query(Users).filter(Users.chat_id == int(cid)).first()
            user.user_step = step
            db.session.commit()
    except Exception as e:
        logging.exception("Error in set_user_step_to_db error = %s", e)


def get_user_last_search_request_from_db(cid):
    user = db.session.query(Users).filter(Users.chat_id == int(cid)).first()
    return user.search_req_last


def set_user_last_search_request_to_db(message):
    try:
        user = db.session.query(Users).filter(Users.chat_id == int(message.chat.id)).first()
        user.search_req_last = message.text
        db.session.commit()
    except Exception as e:
        logging.exception("Error in set_user_last_search_request_to_db error = %s", e)


def add_user_to_db(message):
    try:
        # if user hasn't used the "/start" command yet:
        user = Users(str(message.chat.first_name), str(message.chat.last_name), int(message.chat.id), None,
                     0)  # save user id, so you could brodcast messages to all users of this bot later
        db.session.add(user)
        db.session.commit()
        count = db.session.query(Users.chat_id).count()
        logging.info("Всего пользователей: " + str(count))
    except Exception as e:
        logging.exception("Error in add_user_to_db error = %s", e)


def count_all_users():
    try:
        number_of_users = db.session.query(Users.chat_id).count()
        return number_of_users
    except Exception as e:
        logging.exception("Error in count_all_users error = %s", e)
        return 0


def set_users_steps(user_step, users_message_search_request):
    """Set steps into variable user_step,but only steps above 0"""
    try:
        for data in db.session.query(Users).order_by(Users.chat_id):
            if data.user_step > 0:
                user_step[data.chat_id] = data.user_step
                users_message_search_request[data.chat_id] = data.search_req_last
    except Exception as e:
        logging.exception("Error in set_users_steps error = %s", e)


def is_user_exist(cid):
    try:
        if db.session.query(Users).filter(Users.chat_id == int(cid)).count() == 1:
            return True
        else:
            return False
    except Exception as e:
        logging.exception("Error in is_user_exist error = %s", e)


# secret_key_to_show_users = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))

logging.debug("All users in DB" + str(count_all_users()))
