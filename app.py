from flask import Flask

app = Flask(__name__)

@app.route('/')
def sample():
    return 'Был получен GET-запрос.'

@app.route('/health')
def health():
    return 'Я живой'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000')