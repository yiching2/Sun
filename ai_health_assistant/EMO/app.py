from flask import Flask, render_template, request
import os, re, json
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from multiagent import MultiAgentManager

# 讀取環境變數中的 Gemini API 金鑰
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

app = Flask(__name__)
agent_manager = MultiAgentManager()

# 問題清單
QUESTIONS = [
    "你今天有運動嗎？做了什麼？",
    "你今天吃得健康嗎？吃了哪些食物？",
    "昨晚睡了幾個小時？有睡好嗎？",
    "你今天的心情如何？",
    "有沒有身體不適（頭痛、胃痛、疲倦等等）？"
]

@app.route("/", methods=["GET", "POST"])
def index():
    result = advice = reply_text = user_input = None
    answers = []

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "diary":
            answers = [request.form.get(f"q{i}") for i in range(len(QUESTIONS))]
            diary_text = "\n".join(answers)
            result, advice = agent_manager.analyze(diary_text)
            save_to_csv(answers, result, advice)

        elif form_type == "chat":
            user_input = request.form.get("user_input")
            model = genai.GenerativeModel("gemini-1.5-flash")
            try:
                response = model.generate_content(user_input)
                reply_text = response.text.strip()
                save_chat_to_csv(user_input, reply_text)
            except Exception as e:
                reply_text = "⚠️ 回應失敗：" + str(e)

    return render_template(
        "index.html",
        questions=QUESTIONS,
        answers=answers,
        result=result,
        advice=advice,
        user_input=user_input,
        reply_text=reply_text
    )

def evaluate_health_diary(text: str):
    prompt = '''
你是一位健康分析助理，請根據以下描述的內容評估使用者的健康狀況，並使用 JSON 格式回傳下列指標的 1～5 分數：
- 運動程度
- 飲食健康程度
- 睡眠品質
- 心情穩定度
- 身體不適情形
- 總體健康評估

1. 一段 JSON 區塊（請使用 markdown 的 ```json 格式包起來）
2. 接著在 JSON 區塊之後，以 `-----` 分隔，輸出一段「針對 3 分以下項目的建議」文字（用自然語言書寫）
'''
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt + "\n\n日記內容：\n" + text.strip())
        full_text = response.text.strip()
        if "-----" in full_text:
            json_part, advice_part = full_text.split("-----", 1)
        else:
            json_part, advice_part = full_text, ""
        match = re.search(r'```json\s*(\{.*?\})\s*```', json_part, re.DOTALL)
        json_str = match.group(1) if match else json_part.strip()
        result = json.loads(json_str)
        return result, advice_part.strip()
    except Exception as e:
        print("⚠️ 分析錯誤：", e)
        return {}, "⚠️ 無法產生建議"

def save_to_csv(answers, result, advice, filename="uploads/user_diary.csv"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "日期時間": now,
        "Q1 運動": answers[0],
        "Q2 飲食": answers[1],
        "Q3 睡眠": answers[2],
        "Q4 心情": answers[3],
        "Q5 不適": answers[4],
        "運動程度": result.get("運動程度", ""),
        "飲食健康程度": result.get("飲食健康程度", ""),
        "睡眠品質": result.get("睡眠品質", ""),
        "心情穩定度": result.get("心情穩定度", ""),
        "身體不適情形": result.get("身體不適情形", ""),
        "總體健康評估": result.get("總體健康評估", ""),
        "Gemini建議": advice
    }
    df = pd.DataFrame([row])
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, mode='w', header=True, index=False)

def chat_with_gemini():
    print("\n💬 你現在可以詢問健康相關的問題（輸入 exit 結束）：\n")
    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat(history=[])

    while True:
        user_input = input("你：")
        if user_input.strip().lower() == "exit":
            print("👋 感謝使用健康生活助理，祝你健康平安！")
            break
        try:
            response = chat.send_message(user_input)
            reply_text = response.text.strip()
            print("助理：" + reply_text)
            save_chat_to_csv(user_input, reply_text)
        except Exception as e:
            print("⚠️ 回應失敗：", e)

def save_chat_to_csv(user_question, gemini_response, filename="health_diary_log.csv"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "日期時間": now,
        "使用者問題": user_question,
        "Gemini回覆": gemini_response
    }
    df = pd.DataFrame([row])
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, mode='w', header=True, index=False)

if __name__ == "__main__":
    app.run(debug=True)
