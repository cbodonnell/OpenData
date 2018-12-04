import json
import os
import base64

from flask import render_template, jsonify, redirect, flash, url_for, request
from flask_login import current_user, login_user, logout_user, login_required

from server import app, db, MAPBOX_ACCESS_KEY
from classes import *
from forms import LoginForm, RegistrationForm


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stream')
@login_required
def stream_view():

    return render_template(
        'stream.html',
        user=current_user
    )


@app.route('/user/<user_id>')
def user_view(user_id):
    user = User.query.filter_by(id=user_id).first()

    return render_template(
        'user.html',
        user=user
    )


@app.route('/map/<map_id>')
def map_view(map_id):
    map_obj = Map.query.filter_by(id=map_id).first()

    return render_template(
        'map.html',
        mapbox_access_key=MAPBOX_ACCESS_KEY,
        map=map_obj
    )


@app.route('/dataset/<dataset_id>')
def dataset_view(dataset_id):
    dataset = DataSet.query.filter_by(id=dataset_id).first()

    return render_template(
        'dataset.html',
        dataset=dataset
    )


@app.route('/api/dataset/<dataset_id>')
def dataset_api(dataset_id):
    dataset = DataSet.query.filter_by(id=dataset_id).first()

    root = os.path.realpath(os.path.dirname(__file__))
    dataset_url = os.path.join(root, "static/data",
                               *(str(dataset.id), dataset.file))

    if dataset.type == 'json' or dataset.type == 'geojson':
        json_file = json.load(open(dataset_url))
        raw_dataset = jsonify(json_file)
    else:
        raw_dataset = None  # add handlers for other data types

    return raw_dataset


@app.route('/<liked_type>/<liked_id>/likes')
def likes_view(liked_type, liked_id):
    if liked_type == 'map':
        liked = Map.query.filter_by(id=liked_id).first()
    elif liked_type == 'dataset':
        liked = DataSet.query.filter_by(id=liked_id).first()
    else:  # should not occur
        liked = None

    return render_template(
        'likes.html',
        liked=liked,
    )


@app.route('/<reposted_type>/<reposted_id>/reposts')
def reposts_view(reposted_type, reposted_id):
    if reposted_type == 'map':
        reposted = Map.query.filter_by(id=reposted_id).first()
    elif reposted_type == 'dataset':
        reposted = DataSet.query.filter_by(id=reposted_id).first()
    else:  # should not occur
        reposted = None

    return render_template(
        'reposts.html',
        reposted=reposted,
    )


@app.route('/dataset/<referenced_id>/references')
def references_view(referenced_id):
    referenced = DataSet.query.filter_by(id=referenced_id).first()

    return render_template(
        'references.html',
        referenced=referenced
    )


@app.route('/user/<user_id>/followers')
def followers_view(user_id):
    user = User.query.filter_by(id=user_id).first()

    return render_template(
        'followers.html',
        user=user
    )


@app.route('/user/<user_id>/following')
def followed_view(user_id):
    user = User.query.filter_by(id=user_id).first()

    return render_template(
        'following.html',
        user=user
    )


@app.route('/user/<user_id>/liked')
def liked_view(user_id):
    user = User.query.filter_by(id=user_id).first()

    return render_template(
        'liked.html',
        user=user
    )


@app.route('/user/<user_id>/reposted')
def reposted_view(user_id):
    user = User.query.filter_by(id=user_id).first()

    return render_template(
        'reposted.html',
        user=user
    )


@app.route('/tag/<tag_id>')
def tag_view(tag_id):
    tag = Tag.query.filter_by(id=tag_id).first()

    return render_template(
        'tag.html',
        tag=tag
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('stream_view'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('stream_view'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('stream_view'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        login_user(user)
        return redirect(url_for('stream_view'))
    return render_template('register.html', title='Register', form=form)


@app.route('/follow/<user_id>')
def follow(user_id):
    user = User.query.filter_by(id=user_id).first()
    current_user.follow_toggle(user)
    print('followed!')
    return ''


@app.route('/like/<item_type>/<item_id>')
def like(item_type, item_id):
    if item_type == 'map':
        item = Map.query.filter_by(id=item_id).first()
    elif item_type == 'dataset':
        item = DataSet.query.filter_by(id=item_id).first()
    else:
        item = None
    current_user.like_toggle(item)
    return ''


@app.route('/repost/<item_type>/<item_id>')
def repost(item_type, item_id):
    if item_type == 'map':
        item = Map.query.filter_by(id=item_id).first()
    elif item_type == 'dataset':
        item = DataSet.query.filter_by(id=item_id).first()
    else:
        item = None
    current_user.repost_toggle(item)
    return ''


# this is not used
@app.route('/<map_id>/generate_thumbnail', methods=['POST'])
def generate_thumbnail(map_id):
    img_data = request.form['javascript_data']
    img_data = img_data.replace('data:image/png;base64,', '')
    img_data = img_data.encode()

    with open("static/thumbnails/map_" + map_id + "_thumbnail.png", "wb") as fh:
        fh.write(base64.decodebytes(img_data))
    return ''
