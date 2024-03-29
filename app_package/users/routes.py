
from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from app_package.models import sess, engine, text, Base, \
    Users, Blogposts

from app_package.users.utils import send_reset_email, send_confirm_email

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_users = logging.getLogger(__name__)
logger_users.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','users_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_users.addHandler(file_handler)
logger_users.addHandler(stream_handler)


salt = bcrypt.gensalt()


users = Blueprint('users', __name__)


@users.route('/login', methods = ['GET', 'POST'])
def login():
    print('* in login *')
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    page_name = 'Login'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print(f"formDict: {formDict}")
        email = formDict.get('email')

        user = sess.query(Users).filter_by(email=email).first()

        # verify password using hash
        password = formDict.get('password')

        if user:
            if password:
                if bcrypt.checkpw(password.encode(), user.password):
                    login_user(user)

                    return redirect(url_for('main.home'))
                else:
                    flash('Password or email incorrectly entered', 'warning')
            else:
                flash('Must enter password', 'warning')
        # elif formDict.get('btn_login_as_guest'):
        #     user = sess.query(Users).filter_by(id=2).first()
        #     login_user(user)

        #     return redirect(url_for('dash.dashboard', dash_dependent_var='steps'))
        else:
            flash('No user by that name', 'warning')


    return render_template('users/login.html', page_name = page_name)

@users.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    page_name = 'Register'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        new_email = formDict.get('email')

        check_email = sess.query(Users).filter_by(email = new_email).all()
        if len(check_email)==1:
            flash(f'The email you entered already exists you can sign in or try another email.', 'warning')
            return redirect(url_for('users.register'))

        hash_pw = bcrypt.hashpw(formDict.get('password').encode(), salt)
        new_user = Users(email = new_email, password = hash_pw)
        sess.add(new_user)
        sess.commit()


        # Send email confirming succesfull registration
        try:
            send_confirm_email(new_email)
        except:
            flash(f'Problem with email: {new_email}', 'warning')
            return redirect(url_for('users.login'))

        #log user in
        print('--- new_user ---')
        print(new_user)
        login_user(new_user)
        flash(f'Succesfully registered: {new_email}', 'info')
        return redirect(url_for('main.home'))

    return render_template('users/register.html', page_name = page_name)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route('/reset_password', methods = ["GET", "POST"])
def reset_password():
    page_name = 'Request Password Change'
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    # form = RequestResetForm()
    # if form.validate_on_submit():
    if request.method == 'POST':
        formDict = request.form.to_dict()
        email = formDict.get('email')
        user = sess.query(Users).filter_by(email=email).first()
        if user:
        # send_reset_email(user)
            logger_users.info('Email reaquested to reset: ', email)
            send_reset_email(user)
            flash('Email has been sent with instructions to reset your password','info')
            # return redirect(url_for('users.login'))
        else:
            flash('Email has not been registered with What Sticks','warning')

        return redirect(url_for('users.reset_password'))
    return render_template('users/reset_request.html', page_name = page_name)


@users.route('/reset_password/<token>', methods = ["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = Users.verify_reset_token(token)
    logger_users.info('user::', user)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_password'))
    if request.method == 'POST':

        formDict = request.form.to_dict()
        if formDict.get('password_text') != '':
            hash_pw = bcrypt.hashpw(formDict.get('password_text').encode(), salt)
            user.password = hash_pw
            sess.commit()
            flash('Password successfully updated', 'info')
            return redirect(url_for('users.login'))
        else:
            flash('Must enter non-empty password', 'warning')
            return redirect(url_for('users.reset_token', token=token))

    return render_template('users/reset_request.html', page_name='Reset Password')


# @users.route('/nrodrig1_admin', methods=["GET"])
# def nrodrig1_admin():
#     print("PESONAL_EMAIL: ", current_app.config.get('PERSONAL_EMAIL'))
#     admin_user = sess.query(Users).filter_by(email=current_app.config.get('PERSONAL_EMAIL')).first()
#     if admin_user.admin == True:
#         return redirect(url_for('main.home'))
#     if admin_user != None:
#         admin_user.admin = True
#         sess.commit()
#         flash("nrodrig1@gmail updated to admin", "success")
#     return redirect(url_for('main.home'))

