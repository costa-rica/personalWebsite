from sqlalchemy import create_engine, inspect, text
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, \
    Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from flask_login import UserMixin

from app_package.config import config
import os
from datetime import datetime

from dotenv import load_dotenv
from flask_login import LoginManager


login_manager= LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(any_name_for_id_obj):# any_name_for_id_obj can be any name because its an arg that is the user id.
    # This is probably created somewhere inside flask_login when the user gets logged in. But i've not been able to track it.
    return sess.query(Users).filter_by(id = any_name_for_id_obj).first()


load_dotenv()


if not os.path.exists(config.DB_ROOT):
    os.mkdir(config.DB_ROOT)

if not os.path.exists(os.path.join(config.DB_ROOT,"posts")):
    os.mkdir(os.path.join(config.DB_ROOT,"posts"))


Base = declarative_base()
engine = create_engine(config.SQL_URI, echo = False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind = engine)
sess = Session()


class Users(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    email = Column(Text, unique = True, nullable = False)
    password = Column(Text, nullable = False)
    admin = Column(Boolean, default=False)
    time_stamp_utc = Column(DateTime, nullable = False, default = datetime.utcnow)
    blog_posts = relationship('Blogposts', backref='blog_posts', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s=Serializer(config.SECRET_KEY, expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s=Serializer(config.SECRET_KEY)
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return sess.query(Users).get(user_id)

    def __repr__(self):
        return f'Users(id: {self.id}, email: {self.email})'



class Blogposts(Base):
    __tablename__ = 'blogposts'
    id = Column(Integer, primary_key = True)
    post_id_name_string = Column(String(10))
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(Text)
    description = Column(Text)
    post_html_filename = Column(Text)
    date_published = Column(DateTime)
    time_stamp_utc = Column(DateTime, nullable = False, default = datetime.utcnow)


    def __repr__(self):
        return f"blogposts(id: {self.id}, user_id: {self.user_id}, title: {self.title}, " \
            f"date_published: {self.date_published})"


if 'users' in inspect(engine).get_table_names():
    print("db already exists")
else:
    Base.metadata.create_all(engine)
    print("NEW db created.")