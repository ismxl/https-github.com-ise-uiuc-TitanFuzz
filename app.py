from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify(message='Hello from TitanFuzz example app')


@app.route('/echo', methods=['POST'])
def echo():
    """Echo endpoint that intentionally raises on certain inputs to demonstrate fuzzing.

    Expects JSON: {"data": "..."}
    Raises ValueError if the string contains the substring 'CRASH' or is longer than 2000 chars.
    """
    from flask import request
    j = request.get_json(silent=True) or {}
    s = str(j.get('data', ''))
    # Intentional crash conditions for fuzzing demo
    if 'CRASH' in s:
        raise ValueError('Triggered CRASH substring')
    if len(s) > 2000:
        # Simulate resource exhaustion crash
        raise RuntimeError('Input too large')
    return jsonify(length=len(s), sample=s[:80])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
