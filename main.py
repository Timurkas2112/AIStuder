from flask import Flask, render_template, request, redirect, flash, session
import markdown
from classes import app, User, Group, GroupMember, GroupTeacher, Course, CourseChapter, bcrypt, db
from sqlalchemy.orm import joinedload

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

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)
    
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

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из аккаунта.', 'success')
    return redirect('/')

@app.route('/create_course')
def create_course():
    return render_template("create_course.html")


@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if 'user_id' not in session:
        flash('Вы должны войти в систему', 'error')
        return redirect('/')

    current_user = User.query.get(session['user_id'])
    if current_user.role != 'teacher':
        flash('Только преподаватели могут создавать группы', 'error')
        return redirect('/')

    if request.method == 'POST':
        group_name = request.form['group_name']

        # Создание новой группы
        new_group = Group(name=group_name)
        db.session.add(new_group)
        db.session.flush()  # Нужно, чтобы получить group_id до связывания

        # Добавление студентов
        student_ids_raw = request.form.get('students', '')
        student_ids = [int(sid) for sid in student_ids_raw.split(',') if sid.strip().isdigit()]
        for student_id in student_ids:
            student = User.query.get(student_id)
            if student and student.role == 'student':
                new_group.members.append(student)

        # Автоматическое добавление текущего преподавателя
        new_group.teachers.append(current_user)

        db.session.commit()
        flash('Группа успешно создана!', 'success')
        return redirect('/view_groups')

    # GET-запрос: отдаём только список студентов
    students = User.query.filter_by(role='student').all()
    return render_template('create_group.html', students=students)



# Страница для просмотра всех групп
@app.route('/view_groups')
def view_groups():
    groups = Group.query.all()
    return render_template('view_groups.html', groups=groups)


@app.route('/quiz')
def quiz():
    return render_template("quiz.html", book_content=book_content, quiz_title=quiz_data['title'], questions=quiz_data['questions'])

@app.route("/my_courses")
def my_courses():
    user_id = session.get('user_id')
    
    if not user_id:
        flash("Сначала войдите в систему", "error")
        return redirect('/')

    user = User.query.get(user_id)
    session['role'] = user.role
    # Получаем список групп пользователя
    if user.role == 'student':
        group_ids = [g.group_id for g in user.students_in_groups]
    elif user.role == 'teacher':
        group_ids = [g.group_id for g in user.groups_as_teacher]
    else:
        group_ids = []

    # Получаем только курсы из этих групп
    courses = Course.query.options(
        joinedload(Course.group),
        joinedload(Course.teacher)
    ).filter(Course.group_id.in_(group_ids)).all()

    return render_template("my_courses.html", courses=courses)



@app.route("/create_manual", methods=["GET", "POST"])
def create_manual():
    selected_group_id = None
    if request.method == 'POST':
        group_id = int(request.form['group_id'])
        selected_group_id = group_id

        title = request.form.get("courseTitle")
        new_course = Course(title=title, group_id=group_id)

        db.session.add(new_course)
        db.session.flush()  # Получить course_id

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
    user_id = session.get("user_id")
    groups = Group.query.join(Group.teachers).filter(User.user_id == user_id).all()
    return render_template('create_manual.html', groups=groups, selected_group_id=selected_group_id)




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
    user_id = session.get("user_id")
    course = Course.query.get_or_404(id)
    book_content = get_course_chapters(course_id=id)
    groups = Group.query.join(Group.teachers).filter(User.user_id == user_id).all()
    selected_group_id = course.group_id if course.group_id else None

    if request.method == 'POST':
        # Обновляем главы
        for key in request.form:
            if key.startswith("title_"):
                parts = key.split("_")
                if len(parts) < 2 or not parts[1].isdigit():
                    continue
                chapter_id = int(parts[1])
                title = request.form[key]
                content = request.form.get(f"content_{chapter_id}")
                update_chapter(chapter_id, title, content)

        # Обновляем группу курса
        group_id = request.form.get("group_id")
        if group_id and group_id.isdigit():
            course.group_id = int(group_id)
            db.session.commit()

        return redirect('/my_courses')

    return render_template(
        "edit_course.html",
        book_content=book_content,
        course_id=id,
        groups=groups,
        selected_group_id=selected_group_id
    )





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