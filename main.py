import logging
import random

from flask_socketio import *

from CONFIG import DEFAULT_PORT
from CONFIG import SECRET_KEY
from CONFIG import SERVER_HOST, SERVER_PORT
from silk.config import wpan_constants as wpan
from silk.node.DevBoardNode import DevBoardNode
from silk.node.wpan_node import WpanCredentials
from silk.tools import wpan_table_parser
from errors import OTNSCliError

ML_PREFIX_1 = 'fd00:1::'

app = flask.Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, async_mode='threading')


@app.route('/', methods=['GET'])
def index():
    router = DevBoardNode()
    scan_result = wpan_table_parser.parse_scan_result(router.get_active_scan())
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


@app.route('/form', methods=['GET', 'POST'])
def form():
    device = DevBoardNode()
    prefixes = wpan_table_parser.parse_on_mesh_prefix_result(device.get(wpan.WPAN_THREAD_ON_MESH_PREFIXES))
    network_scope = {
        'networkName': device.get(wpan.WPAN_NAME)[1:-1],
        'extPanId': device.get(wpan.WPAN_XPANID)[2:],
        'panId': device.get(wpan.WPAN_PANID),
        'passphrase': '123456',
        'networkKey': device.get(wpan.WPAN_KEY)[1:-1],
        'channel': device.get(wpan.WPAN_CHANNEL),
        'prefix': prefixes[0].prefix,
        'defaultRoute': True,
    }
    network_data = WpanCredentials(network_name="OpenThreadDemo{0}".format(random.randint(0, 10)),
                                   psk="00112233445566778899aabbccdd{0:04x}".format(random.randint(0, 0xffff)),
                                   channel=random.randint(11, 25),
                                   fabric_id="{0:06x}dead".format(random.randint(0, 0xffffff)))
    # device.form(network_data, "router", mesh_local_prefix=ML_PREFIX_1)
    return flask.render_template('form.html', name='form')


@app.route('/status', methods=['GET'])
def status():
    router = DevBoardNode()
    status = router.handle_status_request()
    return flask.render_template('status.html', title='Status', name='node', status=status)


@app.route('/commission')
def commission():
    return flask.render_template('commission.html', name='commission')


@app.route('/neighbors', methods=['GET'])
def neighbors():
    device = DevBoardNode()
    neighbor_table_text = device.wpanctl("get", "neighbor table", 2)
    print()
    print(neighbor_table_text)
    print()
    neighbor_table = wpan_table_parser.parse_neighbor_table_result(neighbor_table_text)
    return flask.render_template('neighbors.html', title='Neighbors list', name='neighbors',
                                 neighbor_table=neighbor_table, )


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("thread-web").setLevel(logging.DEBUG)
    socketio.run(app=app, host=SERVER_HOST, debug=True, port=SERVER_PORT, use_reloader=True)


if __name__ == "__main__":
    main()
