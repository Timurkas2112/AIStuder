from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5433/AIStuder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    university = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False)

    # Связь с группами через членство и преподавание
    students_in_groups = db.relationship('Group', secondary='group_members', backref=db.backref('members', lazy='dynamic'))
    groups_as_teacher = db.relationship('Group', secondary='group_teachers', backref=db.backref('teachers', lazy='dynamic'))

# Модель для группы
class Group(db.Model):
    __tablename__ = 'groups'
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Таблица связи для студентов
class GroupMember(db.Model):
    __tablename__ = 'group_members'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id', ondelete='CASCADE'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)

# Таблица связи для преподавателей
class GroupTeacher(db.Model):
    __tablename__ = 'group_teachers'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id', ondelete='CASCADE'), primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)


class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'), nullable=True)

    chapters = db.relationship('CourseChapter', backref='course', cascade="all, delete-orphan")
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'))
    group = db.relationship('Group', backref='courses')
    teacher = db.relationship('User', backref='courses')


class CourseChapter(db.Model):
    __tablename__ = 'course_chapters'
    chapter_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete="CASCADE"), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    
    # Связь один-к-одному с тестом
    quiz = db.relationship('Quiz', backref='chapter', uselist=False, cascade="all, delete-orphan")

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    quiz_id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('course_chapters.chapter_id', ondelete="CASCADE"), unique=True)  # Один тест → одна глава
    title = db.Column(db.String(255), nullable=False, default="Тест к главе")
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete="CASCADE"), nullable=False)  # Добавлено
    questions = db.relationship('QuizQuestion', backref='quiz', cascade="all, delete-orphan")

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    question_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id', ondelete="CASCADE"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.ARRAY(db.Text), nullable=False)  # Массив вариантов
    correct_answer = db.Column(db.Text, nullable=False)  # Может быть "1" или "1,3" для нескольких
    question_type = db.Column(db.String(10), nullable=False, default='single')  # Добавляем поле для типа вопроса
    explanation = db.Column(db.Text)