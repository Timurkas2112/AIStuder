from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:1234@localhost:5433/AIStuder"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    university = Column(String, nullable=True)
    role = Column(String, nullable=False)

    # Relationship to groups as a student
    groups = relationship('GroupMember', back_populates='student')

    # Relationship to courses as a teacher
    teaching_groups = relationship('GroupTeacher', back_populates='teacher')

    # Relationship to courses as a teacher
    courses = relationship('Course', back_populates='teacher')


class Group(Base):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    members = relationship('GroupMember', back_populates='group')
    teachers = relationship('GroupTeacher', back_populates='group')
    courses = relationship('Course', back_populates='group')


class GroupMember(Base):
    __tablename__ = 'group_members'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    student_id = Column(Integer, ForeignKey('users.user_id'))

    group = relationship('Group', back_populates='members')
    student = relationship('User', back_populates='groups')


class GroupTeacher(Base):
    __tablename__ = 'group_teachers'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    teacher_id = Column(Integer, ForeignKey('users.user_id'))

    group = relationship('Group', back_populates='teachers')
    teacher = relationship('User', back_populates='teaching_groups')


class Course(Base):
    __tablename__ = 'courses'

    course_id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.user_id'))
    group_id = Column(Integer, ForeignKey('groups.group_id'))

    teacher = relationship('User', back_populates='courses')
    group = relationship('Group', back_populates='courses')
    chapters = relationship('CourseChapter', back_populates='course')


class CourseChapter(Base):
    __tablename__ = 'course_chapters'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.course_id'))
    chapter = Column(Integer)
    title = Column(String(200))
    content = Column(Text)

    course = relationship('Course', back_populates='chapters')


class Quiz(Base):
    __tablename__ = 'quizzes'

    quiz_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.course_id'))
    title = Column(String(200))
    num_questions = Column(Integer)

    questions = relationship('QuizQuestion', back_populates='quiz')


class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.quiz_id'))
    question_text = Column(Text)
    options = Column(ARRAY(Text))  # PostgreSQL ARRAY
    correct_answer = Column(Text)
    explanation = Column(Text)

    quiz = relationship('Quiz', back_populates='questions')
