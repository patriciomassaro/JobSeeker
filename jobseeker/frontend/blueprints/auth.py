import os
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from werkzeug.security import check_password_hash, generate_password_hash
from jobseeker.database import DatabaseManager
from jobseeker.database.models import Users

db = DatabaseManager()
auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()



db=DatabaseManager()
auth_bp = Blueprint('auth', __name__)
AUTH_PATH= 'auth'
LOGIN_HTML = os.path.join(AUTH_PATH, 'login.html')
SIGNUP_HTML = os.path.join(AUTH_PATH, 'signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.form['email']  # It seems you meant to use 'email' as the form name but filter by 'username'
        password = request.form['password']
        with db as session:
            user = session.query(Users).filter(Users.email==email).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect('/')
            else:
                return render_template(LOGIN_HTML,
                                    user = current_user,
                                    error='Invalid username or password')
    else:
        return render_template(LOGIN_HTML, user = current_user)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated and request.method == 'GET':
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        with db as session:
            existing_user = session.query(Users).filter((Users.email == email)).first()
            if existing_user:
                return render_template(SIGNUP_HTML, error='User already exists', user = current_user)

            hashed_password = generate_password_hash(password)
            new_user = Users(name=name, email=email, password=hashed_password)
            session.add(new_user)
            session.commit()
            login_user(new_user)
        return redirect('/')
    return render_template(SIGNUP_HTML, user = current_user)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))