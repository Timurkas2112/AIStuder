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



quiz_data = {
    'title': 'Работа со строками и списками в Python',
    'questions': [
        {
            'id': 1,
            'question_text': 'Какой оператор используется для конкатенации (объединения) строк в Python?',
            'options': ['+', '-', '*', '/'],
            'correct_answer': '+',
            'explanation': 'Оператор "+" используется для сложения (конкатенации) строк.'
        },
        {
            'id': 2,
            'question_text': 'Что произойдет, если применить оператор "*" к строке и числу?',
            'options': [
                'Возникнет ошибка',
                'Строка будет повторена указанное число раз',
                'Строка будет умножена на число',
                'Число будет добавлено к строке'
            ],
            'correct_answer': 'Строка будет повторена указанное число раз',
            'explanation': 'Оператор "*" повторяет строку указанное количество раз.'
        },
        {
            'id': 3,
            'question_text': 'Как получить доступ к третьему символу строки "Python"?',
            'options': ['string[3]', 'string[2]', 'string[-3]', 'string[4]'],
            'correct_answer': 'string[2]',
            'explanation': 'Индексация в Python начинается с 0.  Третий символ имеет индекс 2.'
        },
        {
            'id': 4,
            'question_text': 'Какой метод используется для преобразования строки в верхний регистр?',
            'options': ['lower()', 'upper()', 'capitalize()', 'title()'],
            'correct_answer': 'upper()',
            'explanation': 'Метод upper() преобразует строку в верхний регистр.'
        },
        {
            'id': 5,
            'question_text': 'Что возвращает метод `split()` для строки "Это строка с пробелами"?',
            'options': [
                '"Это строка с пробелами"',
                '["Это", "строка", "с", "пробелами"]',
                '["Это строка с пробелами"]',
                'Ошибка'
            ],
            'correct_answer': '["Это", "строка", "с", "пробелами"]',
            'explanation': 'Метод split() разделяет строку на список подстрок по разделителю (пробелу по умолчанию).'
        },
        {
            'id': 6,
            'question_text': 'Как добавить элемент в конец списка?',
            'options': ['list.append(element)', 'list.insert(0, element)', 'list.extend(element)', 'list.add(element)'],
            'correct_answer': 'list.append(element)',
            'explanation': 'Метод append() добавляет элемент в конец списка.'
        },
        {
            'id': 7,
            'question_text': 'Какой метод удаляет и возвращает последний элемент списка?',
            'options': ['list.remove()', 'list.pop()', 'list.del()', 'list.delete()'],
            'correct_answer': 'list.pop()',
            'explanation': 'Метод pop() удаляет и возвращает последний элемент списка (или элемент по указанному индексу).'
        },
        {
            'id': 8,
            'question_text': 'Являются ли списки в Python изменяемыми?',
            'options': ['Да', 'Нет'],
            'correct_answer': 'Да',
            'explanation': 'Списки в Python являются изменяемыми, в отличие от строк.'
        },
        {
            'id': 9,
            'question_text': 'Что такое срезы (slices) в Python?',
            'options': [
                'Способ удаления элементов из списка',
                'Способ извлечения подпоследовательности из строки или списка',
                'Способ сортировки списка',
                'Способ объединения списков'
            ],
            'correct_answer': 'Способ извлечения подпоследовательности из строки или списка',
            'explanation': 'Срезы позволяют извлечь часть строки или списка.'
        },
        {
            'id': 10,
            'question_text': 'Можно ли в одном списке хранить элементы разных типов данных?',
            'options': ['Да', 'Нет'],
            'correct_answer': 'Да',
            'explanation': 'Списки в Python могут содержать элементы различных типов данных.'
        }
    ]
}