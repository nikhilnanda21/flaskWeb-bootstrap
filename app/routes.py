from flask import render_template, flash, redirect, url_for, session
from app import app
from app.forms import LoginForm, EditProfileForm
from flask_login import current_user, login_user
from app.models import User
from flask_login import logout_user
from flask_login import login_required
from flask import request
from werkzeug.urls import url_parse
from app import db
from app.forms import RegistrationForm
from datetime import datetime

from app.forms import ResetPasswordRequestForm

from datetime import timedelta

globalVar = 1
ind = 25

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            flash('Invalid username')
            return redirect(url_for('reset_password_request'))
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

from app.forms import ResetPasswordForm

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data, duration=timedelta(seconds=30))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.leagueId = form.leagueId.data
        current_user.teamId = form.teamId.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        if current_user.leagueId:
            form.leagueId.data = current_user.leagueId
        if current_user.teamId:
            form.teamId.data = current_user.teamId
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/highlights')
@login_required
def high():
    return render_template('highlights.html')

import urllib.request
from flask import jsonify
import json

@app.route('/live')
@login_required
def live():
    if not current_user.leagueId:
        dummy = "1639"
        return render_template('subscribe.html')
    else:
        dummy = current_user.leagueId
    url = "http://api.isportsapi.com/sport/football/topscorer?api_key=hCfaYXgl0NG0WHBZ&leagueId=" + dummy
    f = urllib.request.urlopen(url)
    content = f.read()
    content = json.loads(content)
    numRow = len(content["data"])

    return render_template('data.html', content=content["data"], numRow=numRow)

@app.route('/player')
@login_required
def player():
    if not current_user.teamId:
        dummy = "26"
        return render_template('subscribe.html')
    else:
        dummy = current_user.teamId
    url = "http://api.isportsapi.com/sport/football/player?api_key=hCfaYXgl0NG0WHBZ&teamId=" + dummy
    f = urllib.request.urlopen(url)
    content = f.read()
    content = json.loads(content)
    numRow = len(content["data"])
    return render_template('player.html', content=content["data"], numRow=numRow)

@app.route('/result')
@login_required
def result():
    if not current_user.leagueId:
        dummy = "1639"
        return render_template('subscribe.html')
    else:
        dummy = current_user.leagueId
    url = "http://api.isportsapi.com/sport/football/schedule?api_key=hCfaYXgl0NG0WHBZ&leagueId=" + dummy
    f = urllib.request.urlopen(url)
    content = f.read()
    content = json.loads(content)
    numRow = len(content["data"])
    return render_template('result.html', content=content["data"], numRow=numRow)

@app.route('/team')
@login_required
def team():
    url = "http://api.isportsapi.com/sport/football/team?api_key=hCfaYXgl0NG0WHBZ"
    f = urllib.request.urlopen(url)
    content = f.read()
    content = json.loads(content)
    numRow = 250
    globalVar = content["data"]
    return render_template('team.html', content=content["data"], numRow=numRow, tmId=current_user.teamId)

@app.route('/idChange/<int:i>', methods=['GET', 'POST'])
def idChange(i):
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.leagueId = form.leagueId.data
        current_user.teamId = form.teamId.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    else:
        url = "http://api.isportsapi.com/sport/football/team?api_key=hCfaYXgl0NG0WHBZ"
        f = urllib.request.urlopen(url)
        content = f.read()
        content = json.loads(content)
        globalVar = content["data"]
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.leagueId.data = globalVar[i]["leagueId"]
        form.teamId.data = globalVar[i]["teamId"]
    return render_template('edit_profile.html', title='Edit Profile', form=form)
