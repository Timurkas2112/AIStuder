from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import markdown

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5433/AIStuder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Group(db.Model):
    __tablename__ = 'groups'
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    university = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False)



class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'), nullable=True)

    chapters = db.relationship('CourseChapter', backref='course', cascade="all, delete-orphan")


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

def update_chapter(chapter_id, title, content):
    chapter = CourseChapter.query.get(chapter_id)
    if chapter:
        chapter.title = title
        chapter.content = content
        db.session.commit()


def update_course(course_id, chapter, title, content):
    # Здесь будет код для обновления курса в базе данных
    pass

def get_course_chapters(course_id):
    return CourseChapter.query.filter_by(course_id=course_id).order_by(CourseChapter.chapter_number).all()

# @app.route('/')
# def index():
#     return render_template("content.html", book_content=book_content)

@app.route('/')
def index():
    return render_template("login.html")

@app.route('/auth', methods=['POST'])
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
            flash('Успешный вход!', 'success')
            return redirect('/')
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


@app.route('/create_course')
def create_course():
    return render_template("create_course.html")




@app.route('/quiz')
def quiz():
    return render_template("quiz.html", book_content=book_content, quiz_title=quiz_data['title'], questions=quiz_data['questions'])

@app.route("/my_courses")
def my_courses():
    courses = Course.query.all()
    return render_template("my_courses.html", courses=courses)



@app.route("/create_manual", methods=["GET", "POST"])
def create_manual():
    if request.method == "POST":
        title = request.form.get("courseTitle")
        new_course = Course(title=title)

        db.session.add(new_course)
        db.session.flush()  # Чтобы получить course_id до коммита

        chapters = []
        index = 1
        while True:
            chapter_title = request.form.get(f"chapterTitle{index}")
            chapter_content = request.form.get(f"chapterContent{index}")
            if not chapter_title:
                break
            chapter = CourseChapter(
                course_id=new_course.course_id,
                chapter_number=index,
                title=chapter_title,
                content=chapter_content
            )
            chapters.append(chapter)
            index += 1

        db.session.add_all(chapters)
        db.session.commit()

        return redirect('/my_courses')

    return render_template("create_manual.html")



@app.route('/course/<int:course_id>')
def view_course(course_id):
    # Получаем главы из базы
    chapters = CourseChapter.query.filter_by(course_id=course_id).order_by(CourseChapter.chapter_number).all()

    return render_template('content.html', book_content=chapters)


@app.route('/course/<int:course_id>/delete')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    try:
        db.session.delete(course)
        db.session.commit()
        flash('Курс успешно удалён.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении курса: {str(e)}', 'danger')

    return redirect('/my_courses')



@app.route('/answers', methods=['POST'])
def answers():
    user_answers = {key: value for key, value in request.form.items()}
    score, total_questions = calculate_score(user_answers)
    return render_template('result.html', book_content=book_content, title='Quiz Result', score=score, total_questions=total_questions)


@app.route('/edit_course/<int:id>', methods=['GET', 'POST'])
def edit_course(id):
    if request.method == 'POST':
        for key in request.form:
            if key.startswith("title_"):
                parts = key.split("_")
                if len(parts) < 2 or not parts[1].isdigit():
                    continue  # пропустить некорректные ключи

                chapter_id = int(parts[1])
                title = request.form[key]
                content = request.form.get(f"content_{chapter_id}")

                update_chapter(chapter_id, title, content)

        return redirect('/my_courses')


    # Предположим, ты получаешь главы вот так:
    book_content = get_course_chapters(course_id=id)

    return render_template("edit_course.html", book_content=book_content, course_id=id)




def calculate_score(user_answers):
    score = 0
    total_questions = len(quiz_data['questions'])

    for question in quiz_data['questions']:
        question_id = question['id']
        user_answer = user_answers.get(str(question_id))  # Convert question_id to string
        if user_answer and user_answer == question['correct_answer']:
            score += 1

    return score, total_questions



if __name__ == "__main__":
    app.run(debug=True)