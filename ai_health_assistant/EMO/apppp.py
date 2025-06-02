from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "🚀 Flask 成功跑起來了！Hello 小潘 👋"

if __name__ == "__main__":
    app.run(debug=True)
