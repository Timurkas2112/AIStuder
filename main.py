from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from classes import app, User, Group, GroupMember, GroupTeacher, Course, CourseChapter, Quiz, QuizQuestion, bcrypt, db
from sqlalchemy.orm import joinedload


from routes import register_blueprints
register_blueprints(app)


if __name__ == "__main__":
    app.run(debug=True)