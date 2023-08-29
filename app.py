from flask import Flask, jsonify
from flask_cors import CORS

from app_lib import AppLib

app = Flask(__name__)
CORS(app)  # This enables CORS for your entire app

app_lib = AppLib()

@app.route('/get_paper_detail/<string:title>', methods=['GET'])
def get_paper_detail(title):
    return jsonify(app_lib.search(title))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)