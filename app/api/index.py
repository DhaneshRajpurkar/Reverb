from flask import Flask

app = Flask(__name__)

@app.route('/template')
def home():
    return 'Hello, World! Welcome to the API sample from Dhanesh.. using Vercel-Flask-Template'

@app.route('/template/about')
def about():
    return 'you have reached the endpoint About -- this one only shows that the vercel-flask-template works with any endpoint'