
from flask import Blueprint, request, jsonify, render_template, session, redirect, flash
from classes import app, User, Group, GroupMember, GroupTeacher, Course, CourseChapter, Quiz, QuizQuestion, bcrypt, db
import tiktoken
from txt_to_blocks import count_tokens, split_by_tokens, extract_text_from_pdf
from generator import get_chapter, fix_invalid_escapes, generate_quiz_for_chapter
import json
import re

creator = Blueprint('course', __name__)

cancel_flags = {}
@creator.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)
def update_chapter(chapter_id, title, content):
    chapter = CourseChapter.query.get(chapter_id)
    if chapter:
        chapter.title = title
        chapter.content = content
        db.session.commit()

@creator.route('/cancel_generation', methods=['POST'])
def cancel_generation():
    user_id = session.get('user_id')
    if user_id:
        cancel_flags[user_id] = True
        return jsonify({'success': True, 'message': 'Генерация отменена'})
    return jsonify({'error': 'Неавторизованный доступ'}), 401


@creator.route('/generate_course', methods=['GET', 'POST'])
def generate_course():
    try:
        # Проверяем авторизацию
        if 'user_id' not in session:
            return jsonify({'error': 'Авторизуйтесь, чтобы создать курс'}), 401
            # GET запрос - показываем форму
        if request.method == 'GET':
            groups = Group.query.all()
            return render_template('create_course.html', groups=groups)

        # Получаем данные из формы
        course_title = request.form.get('courseTitle')
        group_id = request.form.get('studentGroup')
        preferences = request.form.get('preferences', '')
        content_type = request.form.get('contentType')

        # Проверяем обязательные поля
        if not course_title or not group_id:
            return jsonify({'error': 'Укажите название курса и группу'}), 400

        PDF_PATH = "/Users/timursaitbatalov/Downloads/978-5-7996-1198-9_2014.pdf"  # путь к вашему PDF
        TOKEN_LIMIT = 4000
        ENCODING_NAME = "cl100k_base"  # для GPT-4 и GPT-3.5-turbo

        # === Инициализация токенизатора ===
        encoding = tiktoken.get_encoding(ENCODING_NAME)

        full_text = extract_text_from_pdf(PDF_PATH)
        blocks = split_by_tokens(full_text, TOKEN_LIMIT)

        # Генерируем главы
        chapters = []
        structure = ''
        count = 0
        for i in blocks:

            if cancel_flags.get(session['user_id']):
                cancel_flags.pop(session['user_id'], None)
                return jsonify({'error': 'Генерация отменена пользователем'}), 400

            count+=1
            if len(chapters) != 0 and chapters[-1]['status'] == "incomplete":
                structure = "Вот последняя глава, которую ты сгенерировал, здесь status incomplete, поэтому тебе надо продолжить эту главу (добавить материал с начала главы и id главы оставить таким же) и можешь начать следующую главу, если считаешь нужным, в таком случае ты выведешь два словаря" + str(chapters[-1])
            elif len(chapters) != 0 and chapters[-1]['status'] == "complete":
                structure = f" В предыдущей раз ты сгенерировал следующий chapter id: {str(chapters[-1]['chapter_id'])}, поэтому продолжи генерировать с chapter_id: {int(chapters[-1]['chapter_id']) + 1}" 
            raw_json = get_chapter(i, structure)
            cleaned_json = fix_invalid_escapes(raw_json)
            print(f"\n Вывод ИИ:" + cleaned_json)
            try:
                chapter_data = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                raw_json = get_small_chapter(raw_json)
                cleaned_json = fix_invalid_escapes(raw_json)
                print((f"\n Исправленный код ИИ:" + cleaned_json))
                chapter_data = json.loads(cleaned_json)
        
            if isinstance(chapter_data, list):
                for chapter_dict in chapter_data:
                    if len(chapters) != 0 and chapters[-1]['status'] == "incomplete":
                        chapters[-1] = chapter_dict  # Перезаписываем неполную главу
                    else:
                        chapters.append(chapter_dict)  # Добавляем новую главу
            else:
                # Если получен один словарь (одна глава)
                if len(chapters) != 0 and chapters[-1]['status'] == "incomplete":
                    chapters[-1] = chapter_data  # Перезаписываем неполную главу
                else:
                    chapters.append(chapter_data)  # Добавляем новую главу
            if count == 2:
                break

        # Создаем курс в БД
        new_course = Course(
            title=course_title,
            teacher_id=session['user_id'],
            group_id=group_id
        )
        db.session.add(new_course)
        db.session.flush()  # Получаем course_id

        # Добавляем главы
        for i, chapter in enumerate(chapters, start=1):
            if cancel_flags.get(session['user_id']):
                cancel_flags.pop(session['user_id'], None)
                return jsonify({'error': 'Генерация отменена пользователем'}), 400
            new_chapter = CourseChapter(
                course_id=new_course.course_id,
                chapter_number=i,
                title=chapter['title'],
                content=chapter['content']
            )
            db.session.add(new_chapter)
            db.session.flush()
            # # Если нужны тесты - генерируем их
            if content_type in ['lecture_quiz', 'quiz']:
                quiz = generate_quiz_for_chapter(chapter['content'])
                print(quiz)
                cleaned_json = fix_invalid_escapes(quiz)
                quiz_data = json.loads(cleaned_json)
                new_quiz = Quiz(
                    chapter_id=new_chapter.chapter_id,
                    course_id=new_course.course_id,
                    title=f"Тест к главе {i}"
                )
                db.session.add(new_quiz)
                db.session.flush()
                
            #     # Добавляем вопросы
                for q in quiz_data['questions']:
                    new_question = QuizQuestion(
                        quiz_id=new_quiz.quiz_id,
                        question_text=q['question'],
                        options=q['options'],
                        correct_answer=str(q['correct_answer']),
                        question_type=q.get('type', 'single'),
                        explanation=q.get('explanation', '')
                    )
                    db.session.add(new_question)
        cancel_flags.pop(session['user_id'], None)
        db.session.commit()

            # Удаляем временный файл
            # os.remove(filepath)

        return jsonify({
                'success': True,
                'course_id': new_course.course_id,
                'chapters': len(chapters)
            })

        return jsonify({'error': 'Неподдерживаемый формат файла'}), 400

    except Exception as e:
        db.session.rollback()
        cancel_flags.pop(session['user_id'], None)
        return jsonify({'error': f'Ошибка при создании курса: {str(e)}'}), 500


@creator.route('/create_group', methods=['GET', 'POST'])
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

@creator.route("/create_manual", methods=["GET", "POST"])
def create_manual():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if user.role != 'teacher':
        flash('Только преподаватели могут создавать курсы', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            # Создаем курс
            new_course = Course(
                title=request.form['courseTitle'],
                teacher_id=user.user_id,
                group_id=int(request.form['group_id'])
            )
            db.session.add(new_course)
            db.session.flush()  # Получаем course_id
            
            # Обрабатываем главы
            chapter_index = 1
            while f'chapterTitle{chapter_index}' in request.form:
                # Создаем главу
                new_chapter = CourseChapter(
                    course_id=new_course.course_id,
                    chapter_number=chapter_index,
                    title=request.form[f'chapterTitle{chapter_index}'],
                    content=request.form.get(f'chapterContent{chapter_index}', '')
                )
                db.session.add(new_chapter)
                db.session.flush()  # Получаем chapter_id
                
                # Проверяем, есть ли тест для этой главы
                if f'quizTitle{chapter_index}' in request.form:
                    # Создаем тест для главы (связь один-к-одному)
                    new_quiz = Quiz(
                        title=request.form[f'quizTitle{chapter_index}'],
                        chapter_id=new_chapter.chapter_id,  # Важно: привязываем к главе
                        course_id=new_course.course_id 
                    )
                    db.session.add(new_quiz)
                    db.session.flush()  # Получаем quiz_id
                    
                    # Обрабатываем вопросы теста
                    question_index = 1
                    while f'quizQuestion{chapter_index}_{question_index}' in request.form:
                        # Собираем варианты ответов
                        options = []
                        option_index = 1
                        while f'quizOptions{chapter_index}_{question_index}_{option_index}' in request.form:
                            options.append(request.form[f'quizOptions{chapter_index}_{question_index}_{option_index}'])
                            option_index += 1
                        
                        # Определяем тип вопроса
                        question_type = request.form.get(f'quizType{chapter_index}_{question_index}', 'single')
                        
                        # Обрабатываем правильные ответы
                        if question_type == 'single':
                            correct_answer = request.form.get(f'quizCorrect{chapter_index}_{question_index}', '')
                        else:  # multiple
                            correct_answers = request.form.getlist(f'quizCorrect{chapter_index}_{question_index}[]')
                            correct_answer = ','.join(correct_answers)
                        
                        # Создаем вопрос
                        new_question = QuizQuestion(
                            quiz_id=new_quiz.quiz_id,
                            question_text=request.form[f'quizQuestion{chapter_index}_{question_index}'],
                            options=options,
                            correct_answer=correct_answer,
                            question_type=request.form.get(f'quizType{chapter_index}_{question_index}', 'single'),  # Используем значение по умолчанию
                            explanation=request.form.get(f'quizExplanation{chapter_index}_{question_index}', '')
                        )                           
                        db.session.add(new_question)
                        
                        question_index += 1
                
                chapter_index += 1
            
            db.session.commit()
            flash('Курс успешно создан!', 'success')
            return redirect('/my_courses')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании курса: {str(e)}', 'error')
            app.logger.error(f'Error in create_manual: {str(e)}')
            return redirect(request.url)
    
    # GET запрос
    groups = Group.query.join(GroupTeacher).filter(GroupTeacher.teacher_id == user.user_id).all()
    return render_template('create_manual.html', groups=groups)

@creator.route('/edit_course/<int:id>', methods=['GET', 'POST'])
def edit_course(id):
    user_id = session.get("user_id")
    course = Course.query.get_or_404(id)
    book_content = CourseChapter.query.filter_by(course_id=id).order_by(CourseChapter.chapter_number).all()
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

@creator.route('/course/<int:course_id>/delete')
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