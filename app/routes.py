from flask import render_template
from app import app


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/hello')
def hello():
    return 'Hello world'

