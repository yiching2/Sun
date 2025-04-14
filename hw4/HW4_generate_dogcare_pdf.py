from fpdf import FPDF
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from google import genai
import os
import json

# 載入 API 金鑰
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 評分項目
ITEMS = [
    "活動量是否充足",
    "情緒表現是否穩定",
    "是否有睡眠問題",
    "是否需要飲食調整",
    "是否需要外部刺激（如散步或互動）",
    "是否需要醫療評估",
    "是否建議增加陪伴時間",
    "是否有壓力或焦慮傾向",
    "整體飼養建議評估"
]

# 分析用提示
PROMPT = """你是一位狗狗健康評估助理，請根據以下九項指標，針對我提供的狗狗飼養日記進行分析，請回傳標準 JSON 格式：
- 活動量是否充足（1-5）
- 情緒表現是否穩定（1-5）
- 是否有睡眠問題（1-5）
- 是否需要飲食調整（1-5）
- 是否需要外部刺激（如散步或互動）（1-5）
- 是否需要醫療評估（1-5）
- 是否建議增加陪伴時間（1-5）
- 是否有壓力或焦慮傾向（1-5）
- 整體飼養建議評估（1-5）

請**只輸出** JSON 格式，不要多餘的說明文字。
"""

# 分析一篇日記
def evaluate_diary(text: str) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[PROMPT + f"\n以下是日記內容：\n{text.strip()}"]
        )
        cleaned = response.text.strip()

        # debug 用
        print("\n🔹 LLM 回傳內容：\n", cleaned)

        if cleaned.startswith("```"):
            cleaned = cleaned.strip("```json").strip("```").strip()
        result = json.loads(cleaned)
        for item in ITEMS:
            if item not in result:
                result[item] = ""
        return result
    except Exception as e:
        print("⚠️ JSON 解析失敗：", e)
        return {item: "" for item in ITEMS}

# 產出 PDF
def generate_pdf_report(df_eval, df_diary):
    pdf = FPDF()
    pdf.add_page()

    # 設定中文字型
    font_path = "/System/Library/Fonts/STHeiti Medium.ttc"  # macOS 內建
    pdf.add_font("ChineseFont", "", font_path)
    pdf.add_font("ChineseFont", "B", font_path)

    pdf.set_font("ChineseFont", "B", 16)
    pdf.cell(0, 10, "🐶 狗狗日記健康分析報告", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("ChineseFont", "", 12)
    for i, row in df_eval.iterrows():
        pdf.multi_cell(0, 8, f"📅 {df_diary.iloc[i]['diary']}", align="L")
        pdf.ln(1)
        for col in ITEMS:
            pdf.cell(0, 8, f"{col}：{row[col]}", ln=True)
        pdf.ln(5)

    filename = f"dogcare_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    print(f"✅ 已產出報告：{filename}")

def main():
    print("🔍 分析中，請稍候...")

    csv_file = "../hw2/puppy_diary1.csv"
    df_diary = pd.read_csv(csv_file)
    results = [evaluate_diary(row["diary"]) for _, row in df_diary.iterrows()]
    df_eval = pd.DataFrame(results)

    print("📄 產生 PDF 報告中...")
    generate_pdf_report(df_eval, df_diary)

if __name__ == "__main__":
    main()