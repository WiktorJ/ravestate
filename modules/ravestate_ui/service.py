from flask import Flask, render_template, send_from_directory
from flask import jsonify
from flask_socketio import SocketIO, emit
from ravestate.context import Context

app = Flask(__name__, static_url_path='')

context: Context = None
socketio = SocketIO(app)

@app.route('/scripts/<path:path>')
def send_js(path):
    return send_from_directory('scripts', path)

@app.route('/static/<path:path>')
def send_css(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    global context
    return render_template('index.html')


@app.route('/data')
def get_data():
    global context
    sets = parse_data()
    return jsonify(sets)

def format_whitespace(s, sub, nth):
    find = s.find(sub)
    # loop util we find no match
    i = 1
    while find != -1:
        # if i  is equal to nth we found nth matches so replace
        if i == nth:
            s = s[:find]+"\n"+s[find + len(sub):]
            i = 0
        # find + len(sub) + 1 means we start after the last match
        find = s.find(sub, find + len(sub) + 1)
        i += 1
    return s

def parse_data():
    global context
    sets = []

    for state in context._activations_per_state:
        for target in state.write_props:
            set = {}
            # set['source'] = format_whitespace(state.name, "_", 2).replace("_", " ")
            set['source'] = state.name
            set['target'] = target
            set['type'] = 'changes'
            sets.append(set)
        for signal in state.constraint.signals():
            # Add depended-on signals
            set = {}
            set['source'] = signal.name
            # set['target'] = format_whitespace(state.name, "_", 2).replace("_", " ")
            set['target'] = state.name
            set['type'] = 'triggers'
            sets.append(set)
        if state.signal():
            set = {}
            # set['source'] = format_whitespace(state.name, "_", 2).replace("_", " ")
            set['source'] = state.name
            set['target'] = state.signal().name
            set['type'] = 'emits'
            sets.append(set)

    for property_name, property in context._properties.items():
        for signal in property.signals():
            set = {}
            set['source'] = str(property.id())
            set['target'] = str(signal.name)
            set['type'] = 'sets'
            sets.append(set)


    return sets

@socketio.on('update')
def update():
    sets = parse_data()
    emit('newdata', jsonify(sets))

def advertise(*, ctx, ip="0.0.0.0", port=5000, debug=False):
    global context
    context = ctx
    app.debug=debug
    app.run(ip, port)
    socketio.run(app)