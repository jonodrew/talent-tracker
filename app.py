from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/assets/<path:filename>')
def send_file(filename):
    return send_from_directory('node_modules/govuk-frontend/assets/', filename)


if __name__ == '__main__':
    app.run()
