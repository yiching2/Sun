from flask import Flask, render_template, request
from multiagent import MultiAgentManager

app = Flask(__name__)
agent_manager = MultiAgentManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    diary_text = request.form['diary']
    result = []

    def capture(agent_name, message):
        result.append(f"<b>{agent_name}</b>: {message}")

    final_summary = agent_manager.analyze_diary(diary_text, callback=capture)

    return render_template('index.html', diary=diary_text, analysis="\n".join(result))

if __name__ == '__main__':
    app.run(debug=True)
