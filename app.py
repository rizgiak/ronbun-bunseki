from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This enables CORS for your entire app

@app.route('/get_json_data', methods=['GET'])
def get_json_data():
    # Retrieve JSON data (replace this with your data retrieval logic)
    json_data = {"key": "value"}

    return jsonify(json_data)

if __name__ == '__main__':
    app.run()