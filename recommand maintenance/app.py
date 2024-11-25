from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from usage_DB import User, Product, Purchase

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recommendations.db'
db = SQLAlchemy(app)



if __name__ == '__main__':
    app.run(debug=True)