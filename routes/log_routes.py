from flask import Blueprint, request, jsonify, render_template, session, redirect, flash, Flask, url_for
from classes import User, Group, GroupMember, GroupTeacher, Course, CourseChapter, Quiz, QuizQuestion, bcrypt, db


log = Blueprint('log', __name__)

@log.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)
    
@log.route('/')
def index():
    return render_template("login.html")

@log.route('/auth', methods=['POST'])
def auth():
    form_type = request.form.get('form_type')

    if form_type == 'login':
        identifier = request.form.get('email')  # это может быть email или username
        password = request.form.get('password')

        # Поиск по username или email
        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.user_id  # сохраняем ID пользователя в сессии
            flash('Успешный вход!', 'success')
            return redirect('/my_courses')
        else:
            flash('Неверный email/имя пользователя или пароль', 'error')
            return redirect('/')

    elif form_type == 'register':
        email = request.form.get('email')
        username = request.form.get('username')
        university = request.form.get('university')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Пароли не совпадают', 'error')
            return redirect('/')

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return redirect('/')

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким username уже существует', 'error')
            return redirect('/')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw, university=university, role=role)
        db.session.add(user)
        db.session.commit()

        flash('Вы успешно зарегистрированы!', 'success')
        return redirect('/')

    flash('Неверная форма', 'error')
    return redirect('/')

@log.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из аккаунта.', 'success')
    return redirect('/')
