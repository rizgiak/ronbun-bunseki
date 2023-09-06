from flask import Flask, jsonify
from flask_cors import CORS

from app_lib import AppLib

app = Flask(__name__)
CORS(app)  # This enables CORS for your entire app

app_lib = AppLib()

@app.route('/get_paper_detail/<int:id>', methods=['GET'])
def get_paper_detail(id):
    return jsonify(app_lib.search(id))

@app.route('/get_st/', methods=['GET'])
def get_st():
    return jsonify(app_lib.get_st())

@app.route('/load_data/', methods=['GET'])
def load_data():
    return jsonify(app_lib.load_data())

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)