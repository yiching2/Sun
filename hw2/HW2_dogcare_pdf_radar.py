import os
import json
import time
import pandas as pd
import sys
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

# 載入 .env 中的 GEMINI_API_KEY
load_dotenv()

# 定義狗狗照護評分項目
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

def parse_response(response_text):
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        result = json.loads(cleaned)
        for item in ITEMS:
            if item not in result:
                result[item] = ""
        return result
    except Exception as e:
        print(f"解析 JSON 失敗：{e}")
        print("原始回傳內容：", response_text)
        return {item: "" for item in ITEMS}

def select_dialogue_column(chunk: pd.DataFrame) -> str:
    preferred = ["text", "utterance", "content", "dialogue", "日記內容"]
    for col in preferred:
        if col in chunk.columns:
            return col
    print("CSV 欄位：", list(chunk.columns))
    return chunk.columns[0]

def process_batch_dialogue(client, dialogues: list, delimiter="-----"):
    prompt = (
        "你是一位狗狗日記分析專家，請根據以下項目對每篇狗狗的飼養日記進行照護建議評估，\n每項請以 1~5 分給分，並使用 JSON 格式回覆：\n"
        + "\n".join(ITEMS) +
        "\n\n請依據每篇日記產生 JSON 回覆，每筆之間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "格式範例：\n"
        "```\n"
        "{\n"
        "  \"活動量是否充足\": \"4\",\n"
        "  \"情緒表現是否穩定\": \"5\",\n"
        "  ...\n"
        "}\n"
        "```\n"
    )
    batch_text = f"\n{delimiter}\n".join(dialogues)
    content = prompt + "\n\n" + batch_text

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=content
        )
    except ServerError as e:
        print(f"API 呼叫失敗：{e}")
        return [{item: "" for item in ITEMS} for _ in dialogues]

    print("批次 API 回傳內容：", response.text)
    parts = response.text.split(delimiter)
    results = []
    for part in parts:
        part = part.strip()
        if part:
            results.append(parse_response(part))
    if len(results) > len(dialogues):
        results = results[:len(dialogues)]
    elif len(results) < len(dialogues):
        results.extend([{item: "" for item in ITEMS}] * (len(dialogues) - len(results)))
    return results

def main():
    if len(sys.argv) < 2:
        print("用法：python HW2_dogcare_pdf_radar.py <path_to_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = "dogcare_result.csv"
    if os.path.exists(output_csv):
        os.remove(output_csv)

    df = pd.read_csv(input_csv)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("請設定環境變數 GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_api_key)

    dialogue_col = select_dialogue_column(df)
    print(f"使用欄位作為日記內容欄位：{dialogue_col}")

    batch_size = 10
    total = len(df)
    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        dialogues = batch[dialogue_col].astype(str).tolist()
        dialogues = [d.strip() for d in dialogues]
        batch_results = process_batch_dialogue(client, dialogues)
        batch_df = batch.copy()
        for item in ITEMS:
            batch_df[item] = [res.get(item, "") for res in batch_results]
        if start_idx == 0:
            batch_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        else:
            batch_df.to_csv(output_csv, mode='a', index=False, header=False, encoding="utf-8-sig")
        print(f"已處理 {end_idx} 筆 / {total}")
        time.sleep(1)

    print("🐶 分析完成，結果已寫入：", output_csv)

if __name__ == "__main__":
    main()
