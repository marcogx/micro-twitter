import datetime
import os
from flask.ext.bcrypt import generate_password_hash
from flask.ext.login import UserMixin
from peewee import *

# DATABASE = SqliteDatabase('social.db')
# DATABASE = MySQLDatabase("microtwitter", host="microtwitter.cvxlucsoypjt.us-west-2.rds.amazonaws.com",
#                          port=3306, user="microtwitter", passwd="microtwitter")

DATABASE = Proxy()
DEBUG = True


class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)
    
    class Meta:
        database = DATABASE
        order_by = ('-joined_at',)
        
    def get_posts(self):
        return Post.select().where(Post.user == self)
    
    def get_stream(self):
        return Post.select().where(
            (Post.user << self.following()) |
            (Post.user == self)
        )
    
    def following(self):
        """The users that we are following."""
        return (
            User.select().join(
                Relationship, on=Relationship.to_user
            ).where(
                Relationship.from_user == self
            )
        )
    
    def followers(self):
        """Get users following the current user"""
        return (
            User.select().join(
                Relationship, on=Relationship.from_user
            ).where(
                Relationship.to_user == self
            )
        )
        
    @classmethod
    def create_user(cls, username, email, password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin)
        except IntegrityError:
            raise ValueError("User already exists")
            
            
class Post(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(
        rel_model=User,
        related_name='posts'
    )
    content = TextField()
    
    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)

        
class Relationship(Model):
    from_user = ForeignKeyField(User, related_name='from_relationships')
    to_user = ForeignKeyField(User, related_name='to_relationships')
    
    class Meta:
        database = DATABASE
        indexes = (
            (('from_user', 'to_user'), True),
        )
    

if 'HEROKU' in os.environ:
    import urlparse, psycopg2
    urlparse.uses_netloc.append('postgres')
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
    DATABASE.initialize(db)
    DEBUG = True
else:
    db = SqliteDatabase('micro-twitter.db')
    DATABASE.initialize(db)


def initialize():
    DATABASE.initialize(db)
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship], safe=True)
    DATABASE.close()
