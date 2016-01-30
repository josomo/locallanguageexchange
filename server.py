# server.py
import datetime
import falcon
import json
import os
import requests
from sqlalchemy import Table, Column, Integer, String, Text, MetaData, ForeignKey, create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import current_timestamp

engine = create_engine(os.environ['POSTGRESQL_URL'], echo=True)


Base = declarative_base()
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    learning = Column(String)
    teaching = Column(String)
    bio = Column(Text)

    def __init__(self, name, location, learning, teaching, bio, version=None):
        self.name = name
        self.location = location
        self.learning = learning
        self.teaching = teaching
        self.bio = bio
        self.created_at = datetime.datetime.utcnow().replace(microsecond=0)
        self.updated_at = datetime.datetime.utcnow().replace(microsecond=0)

Session = sessionmaker(bind=engine)
session = Session()


class SearchResource:
    def on_post(self, req, resp):
        raw_body = req.stream.read()
        body = json.loads(raw_body.decode('utf-8'))
        r = requests.get('https://www.zipcodeapi.com/rest/9v7f6irZ6Xab9xOAvyykbPpoNydB01E9wLpD4QCbNNmXkbyQJ6bUWAjJ9xk9yZj5/radius.json/{}/15/mile'.format(body['location']))
        nearby_zips = json.loads(r.text)['zip_codes']
        lst=[]
        for entry in nearby_zips:
            lst.append(entry['zip_code'])
        peeps=[]
        dude={}
        for zip in lst:
            learning=body['teaching'].encode('ascii','ignore')
            teaching=body['learning'].encode('ascii','ignore')
            nears = session.query(User).filter_by(location=zip, learning=learning, teaching=teaching).all()
            if nears:
                for near in nears:
                    dude['name'] = near.name
                    dude['bio'] = near.bio
                    peeps.append(dude)
        resp.body = json.dumps(peeps)


class PostResource:
    def on_post(self, req, resp):
        try:
            raw_body = req.stream.read()
            body = json.loads(raw_body.decode('utf-8'))
            new_guy = User(body['name'], body['location'], body['learning'], body['teaching'], body['bio'])
            session.add(new_guy)
            session.commit()
            resp.status = falcon.HTTP_201
        except:
            resp.status = falcon.HTTP_400

api = falcon.API()
api.add_route('/search', SearchResource())
api.add_route('/post', PostResource())
