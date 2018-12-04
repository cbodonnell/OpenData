# classes.py
from server import db, login, MAPBOX_ACCESS_KEY
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


map_sources = db.Table('map_sources',
                       db.Column('map_id', db.Integer, db.ForeignKey('map.id')),
                       db.Column('source_id', db.Integer, db.ForeignKey('data_set.id')),
                       )

map_layers = db.Table('map_layers',
                      db.Column('map_id', db.Integer, db.ForeignKey('map.id')),
                      db.Column('layer_id', db.Integer, db.ForeignKey('layer.id')),
                      )

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )

likes = db.Table('likes',
                 db.Column('liker_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('liked_data_set_id', db.Integer, db.ForeignKey('data_set.id')),
                 db.Column('liked_map_id', db.Integer, db.ForeignKey('map.id'))
                 )

reposts = db.Table('reposts',
                   db.Column('reposter_id', db.Integer, db.ForeignKey('user.id')),
                   db.Column('reposted_data_set_id', db.Integer, db.ForeignKey('data_set.id')),
                   db.Column('reposted_map_id', db.Integer, db.ForeignKey('map.id'))
                   )
tags = db.Table('tags',
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                   db.Column('tagged_data_set_id', db.Integer, db.ForeignKey('data_set.id')),
                   db.Column('tagged_map_id', db.Integer, db.ForeignKey('map.id'))
                   )


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    join_date = db.Column(db.DateTime, nullable=False,
                          default=datetime.utcnow)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    liked_data_sets = db.relationship(
        'DataSet', secondary=likes,
        backref=db.backref('likes', lazy='dynamic'), lazy='dynamic')

    liked_maps = db.relationship(
        'Map', secondary=likes,
        backref=db.backref('likes', lazy='dynamic'), lazy='dynamic')

    reposted_data_sets = db.relationship(
        'DataSet', secondary=reposts,
        backref=db.backref('reposts', lazy='dynamic'), lazy='dynamic')

    reposted_maps = db.relationship(
        'Map', secondary=reposts,
        backref=db.backref('reposts', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def followed_maps(self):
        followed = Map.query.join(
            followers, (followers.c.followed_id == Map.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Map.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Map.pub_date.desc()).all()

    def followed_datasets(self):
        followed = DataSet.query.join(
            followers, (followers.c.followed_id == DataSet.user_id)).filter(
            followers.c.follower_id == self.id)
        own = DataSet.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(DataSet.pub_date.desc()).all()

    # TODO: Combine maps and datasets into a Posts table with pub_date?
    def all_followed(self):
        followed_maps = Map.query.join(
            followers, (followers.c.followed_id == Map.user_id)).filter(
            followers.c.follower_id == self.id)
        followed_reposted_maps = Map.query.join(
            reposts, (reposts.c.reposted_map_id == Map.id)).join(
            followers, (followers.c.followed_id == reposts.c.reposter_id)).filter(
            followers.c.follower_id == self.id)
        own_maps = Map.query.filter_by(user_id=self.id)
        reposted_maps = Map.query.join(
            reposts, (reposts.c.reposted_map_id == Map.id)).filter(
            reposts.c.reposter_id == self.id)
        maps = followed_maps.union(
            followed_reposted_maps).union(
            own_maps).union(
            reposted_maps).order_by(
            Map.pub_date.desc()).all()
        followed_datasets = DataSet.query.join(
            followers, (followers.c.followed_id == DataSet.user_id)).filter(
            followers.c.follower_id == self.id)
        followed_reposted_datasets = DataSet.query.join(
            reposts, (reposts.c.reposted_data_set_id == DataSet.id)).join(
            followers, (followers.c.followed_id == reposts.c.reposter_id)).filter(
            followers.c.follower_id == self.id)
        own_datasets = DataSet.query.filter_by(user_id=self.id)
        reposted_datasets = DataSet.query.join(
            reposts, (reposts.c.reposted_data_set_id == DataSet.id)).filter(
            reposts.c.reposter_id == self.id)
        datasets = followed_datasets.union(
            followed_reposted_datasets).union(
            own_datasets).union(
            reposted_datasets).order_by(
            DataSet.pub_date.desc()).all()
        followed = maps + datasets
        followed.sort(key=lambda r: r.pub_date, reverse=True)
        return followed

    def follow_toggle(self, user):
        if user not in self.followed:
            self.followed.append(user)
        else:
            self.followed.remove(user)
        db.session.commit()

    def like_toggle(self, item):
        if item.post_type == 'map':
            if item not in self.liked_maps:
                self.liked_maps.append(item)
            else:
                self.liked_maps.remove(item)
        elif item.post_type == 'dataset':
            if item not in self.liked_data_sets:
                self.liked_data_sets.append(item)
            else:
                self.liked_data_sets.remove(item)
        else:  # should not occur
            pass
        db.session.commit()

    def repost_toggle(self, item):
        if item.post_type == 'map':
            if item not in self.reposted_maps:
                self.reposted_maps.append(item)
            else:
                self.reposted_maps.remove(item)
        elif item.post_type == 'dataset':
            if item not in self.reposted_data_sets:
                self.reposted_data_sets.append(item)
            else:
                self.reposted_data_sets.remove(item)
        else:  # should not occur
            pass
        db.session.commit()


class DataSet(db.Model):
    post_type = 'dataset'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(40), nullable=False)
    file = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    pub_date = db.Column(db.DateTime, nullable=False,
                         default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    user = db.relationship('User',
                           backref=db.backref('datasets', lazy=True))

    def __repr__(self):
        return '<DataSet %r>' % self.title


class Map(db.Model):
    post_type = 'map'

    # default MapBox properties
    container = 'map'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    lat = db.Column(db.Float, nullable=False,
                    default=0.)
    lng = db.Column(db.Float, nullable=False,
                    default=0.)
    zoom = db.Column(db.Float, nullable=False,
                     default=0.)
    style = db.Column(db.String(25), nullable=False,
                      default='basic')
    js = db.Column(db.Text)
    pub_date = db.Column(db.DateTime, nullable=False,
                         default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                        nullable=False)
    user = db.relationship('User',
                           backref=db.backref('maps', lazy=True))

    sources = db.relationship(
        'DataSet', secondary=map_sources,
        backref=db.backref('references', lazy='dynamic'), lazy='dynamic')

    layers = db.relationship(
        'Layer', secondary=map_layers, lazy='dynamic')

    def __repr__(self):
        return '<Map %r>' % self.title


class Layer(db.Model):

    popup = None

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(25), nullable=False)
    source_layer = db.Column(db.Text, nullable=False,
                             default='')
    layout = db.Column(db.Text, nullable=False,
                       default='{}')
    paint = db.Column(db.Text, nullable=False,
                      default='{}')

    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'),
                            nullable=False)
    data_set = db.relationship('DataSet',
                               backref=db.backref('layers'), lazy=True)


class Popup(db.Model):
    layer_id = db.Column(db.Integer, db.ForeignKey('layer.id'),
                         nullable=False)
    layer = db.relationship('Layer',
                            backref=db.backref('popups'), lazy=True)
    title = db.Column(db.String(120), nullable=False)
    subtitle = db.Column(db.String(240))
    properties = db.Column(db.Text)
    id = db.Column(db.Text, primary_key=True, nullable=False)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    tagged_maps = db.relationship(
        'Map', secondary=tags,
        backref=db.backref('tags', lazy='dynamic'), lazy='dynamic')

    tagged_data_sets = db.relationship(
        'DataSet', secondary=tags,
        backref=db.backref('tags', lazy='dynamic'), lazy='dynamic')
