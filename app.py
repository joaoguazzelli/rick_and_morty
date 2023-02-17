from flask import Flask
from flask_cors import CORS
from routes.character import create_char

app = Flask(__name__)
CORS(app)
create_char(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
