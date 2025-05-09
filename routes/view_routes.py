from flask import Blueprint, request, jsonify, render_template, session, redirect, flash, Flask, url_for
from classes import User, Group, GroupMember, GroupTeacher, Course, CourseChapter, Quiz, QuizQuestion, bcrypt, db
from sqlalchemy.orm import joinedload
import re

viewer = Blueprint('viewer', __name__)

@viewer.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)
# Страница для просмотра всех групп
@viewer.route('/view_groups')
def view_groups():
    groups = Group.query.all()
    return render_template('view_groups.html', groups=groups)


@viewer.route('/quiz/<int:quiz_id>')
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter = CourseChapter.query.get_or_404(quiz.chapter_id)
    course = Course.query.get_or_404(chapter.course_id)

    chapters = CourseChapter.query.filter_by(course_id=course.course_id).order_by(CourseChapter.chapter_number).all()
    
    current_index = next((i for i, c in enumerate(chapters) if c.chapter_id == chapter.chapter_id), None)

    # Ссылка на предыдущую главу
    prev_chapter_url = url_for('viewer.view_course', course_id=course.course_id) + f'#chapter{chapter.chapter_number}'
    prev_chapter_is_quiz = False

    next_chapter_url = None
    next_chapter_is_quiz = False

    if current_index is not None:
        # Сначала ищем следующую главу
        if current_index < len(chapters) - 1:
            next_chapter = chapters[current_index + 1]
            next_chapter_url = url_for('viewer.view_course', course_id=course.course_id) + f'#chapter{next_chapter.chapter_number}'
            next_chapter_is_quiz = False

        else:
            # Глав больше нет — возможно, есть тест к следующей?
            next_quiz = Quiz.query.filter(Quiz.chapter_id == chapter.chapter_id, Quiz.quiz_id != quiz_id).first()
            if next_quiz:
                next_chapter_url = url_for('take_quiz', quiz_id=next_quiz.quiz_id)
                next_chapter_is_quiz = True

    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
    questions_data = [{
        'id': q.question_id,
        'question_text': q.question_text,
        'options': q.options,
        'correct_answer': q.correct_answer,
        'explanation': q.explanation,
        'question_type': q.question_type
    } for q in questions]

    return render_template(
        'quiz.html',
        quiz=quiz,
        chapter=chapter,
        course=course,
        questions=questions_data,
        quiz_title=quiz.title,
        prev_chapter_url=prev_chapter_url,
        next_chapter_url=next_chapter_url,
        next_chapter_is_quiz=next_chapter_is_quiz
    )

                         
@viewer.route("/my_courses")
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



@viewer.route('/course/<int:course_id>')
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    chapters = CourseChapter.query.filter_by(course_id=course_id).order_by(CourseChapter.chapter_number).all()
    
    # Добавляем информацию о тестах к каждой главе
    for chapter in chapters:
        chapter.quiz = Quiz.query.filter_by(chapter_id=chapter.chapter_id).first()
    
    return render_template('content.html', book_content=chapters, course_title=course.title)
