from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
email = os.getenv("FACEBOOK_EMAIL")
password = os.getenv("FACEBOOK_PASSWORD")

def open_chatgpt_and_ask(question):
    with sync_playwright() as playwright:
        # 打開瀏覽器（不是 headless 才看得到）
        browser = playwright.chromium.launch(headless=False)
        chat_page = browser.new_page()

        print("🔍 正在開啟 ChatGPT 網頁...")

        # 進入 ChatGPT 首頁
        chat_page.goto("https://chatgpt.com/?model=gpt-4o")
        chat_page.wait_for_timeout(5000)

        # 等待輸入區載入
        try:
            editor_area = chat_page.locator("//div[contains(@class, 'ProseMirror')]")
            editor_area.wait_for(state="attached", timeout=10000)
            print("✅ 找到輸入區，可以開始對話了！")
        except Exception as e:
            print("❌ 找不到輸入框，請確認網頁是否正確載入：", e)
            browser.close()
            return

        # 輸入問題
        editor_area.fill(question)
        chat_page.evaluate(
            "document.querySelector('div.ProseMirror').dispatchEvent(new Event('input', { bubbles: true }));"
        )
        chat_page.keyboard.press("Enter")
        print(f"📤 問題已送出：{question}")

        # 等待回覆
        chat_page.wait_for_timeout(10000)

        # 嘗試擷取回答
        try:
            answers = chat_page.locator("div.markdown").all()
            if answers:
                latest = answers[-1].text_content()
                print("🤖 ChatGPT 的回應是：\n", latest)
            else:
                print("⚠️ 沒有擷取到任何回應內容。")
        except Exception as e:
            print("⚠️ 擷取回應時發生錯誤：", e)

        input("🕵️ 查看完畫面後按 Enter 關閉...")
        browser.close()
        print("🛑 瀏覽器關閉，程式結束。")

# 測試：改這裡的文字就能換問題
open_chatgpt_and_ask("幫我推薦三本商業策略書")
