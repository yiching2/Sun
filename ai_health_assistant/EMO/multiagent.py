# multiagent.py
import google.generativeai as genai
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

class MultiAgentManager:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def analyze(self, text):
        prompt = '''
你是一位健康分析助理，請根據以下描述的內容評估使用者的健康狀況，並使用 JSON 格式回傳下列指標的 1～5 分數：
- 運動程度
- 飲食健康程度
- 睡眠品質
- 心情穩定度
- 身體不適情形
- 總體健康評估

請使用 markdown 的 ```json 格式包起來，並在後面用 ----- 隔開建議文字。
'''
        try:
            response = self.model.generate_content(prompt + "\n\n日記內容：\n" + text.strip())
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
            print("⚠️ 多代理分析失敗：", e)
            return {}, "⚠️ 無法產生建議"
