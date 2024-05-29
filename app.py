from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live-feed')
def live_feed():
    return render_template('live-feed.html')

if __name__ == '__main__':
    app.run(debug=True)