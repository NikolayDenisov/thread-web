import logging

from flask_socketio import *

from CONFIG import DEFAULT_PORT
from CONFIG import SECRET_KEY
from CONFIG import SERVER_HOST, SERVER_PORT
from silk.config import wpan_constants as wpan
from silk.node.DevBoardNode import DevBoardNode
from silk.tools import wpan_table_parser

app = flask.Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app)


@app.route('/')
def index():
    router = DevBoardNode()
    scan_result = wpan_table_parser.parse_scan_result(router.get_active_scan(DEFAULT_PORT))
    return flask.render_template('thread_networks.html', title='Available Thread Networks', name='index',
                                 scan_result=scan_result)


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
    router = DevBoardNode()
    status = router.wpanctl("get", "status", 2)
    # Example of expected text:
    #
    # `wpan0 => [\n
    # \t"NCP:State" => "associated"\n
    # \t"Daemon:Enabled" => true\n
    # ]'
    #
    status_result = wpan_table_parser.StatusResult(status)
    return flask.render_template('status.html', name='node', status_result=status_result)


@app.route('/commission')
def commission():
    return flask.render_template('commission.html', name='commission')


@app.route('/neighbors')
def neighbors():
    router = DevBoardNode()
    neighbor_table_text = router.wpanctl("get", "get " + wpan.WPAN_THREAD_NEIGHBOR_TABLE, 2)
    neighbor_table = wpan_table_parser.parse_neighbor_table_result(neighbor_table_text)
    return flask.render_template('neighbors.html', name='neighbors', neighbor_table=neighbor_table)


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("thread-web").setLevel(logging.DEBUG)
    socketio.run(app=app, host=SERVER_HOST, debug=True, port=SERVER_PORT, use_reloader=False)


if __name__ == "__main__":
    main()
