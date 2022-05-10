import logging

from flask_socketio import *

from CONFIG import DEFAULT_PORT
from CONFIG import SECRET_KEY
from CONFIG import SERVER_HOST, SERVER_PORT
from silk.node.DevBoardNode import DevBoardNode
from silk.tools import wpan_table_parser

app = flask.Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app)


@app.route('/')
def index():
    scanner = DevBoardNode()
    scan_result = wpan_table_parser.parse_scan_result(scanner.get_active_scan(DEFAULT_PORT))
    return flask.render_template('index.html', name='index', scan_result=scan_result)


@app.route('/settings')
def settings():
    return flask.render_template('settings.html', name='settings')


@app.route('/login')
def login():
    return flask.render_template('login.html', name='login')


@app.route('/register')
def register():
    return flask.render_template('register.html', name='register')


@app.route('/things')
def things():
    return flask.render_template('things.html', name='things')


@app.route('/resources')
def resources():
    return flask.render_template('resources.html', name='resources')


@app.route('/networks')
def networks():
    return flask.render_template('networks.html', name='networks')


@app.route('/join')
def join():
    return flask.render_template('join.html', name='join')


@app.route('/form')
def form():
    return flask.render_template('form.html', name='form')


@app.route('/status')
def status():
    return flask.render_template('status.html', name='status')


@app.route('/commission')
def commission():
    return flask.render_template('commission.html', name='commission')


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("thread-web").setLevel(logging.DEBUG)
    socketio.run(app=app, host=SERVER_HOST, debug=True, port=SERVER_PORT, use_reloader=False)


if __name__ == "__main__":
    main()
