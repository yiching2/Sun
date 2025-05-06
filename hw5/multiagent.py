import time

# 假設這三個代理人是獨立分析日記的不同面向
class DietAgent:
    def analyze(self, text):
        time.sleep(1)
        return "飲食建議：建議減少狗狗零食攝取，增加蛋白質比例。"

class ActivityAgent:
    def analyze(self, text):
        time.sleep(1)
        return "活動建議：每天至少散步 30 分鐘，有助於健康與情緒穩定。"

class BehaviorAgent:
    def analyze(self, text):
        time.sleep(1)
        return "行為觀察：最近咬玩具的頻率上升，可能是壓力反應。"

# 管理所有 Agent 的主控類別
class MultiAgentManager:
    def __init__(self):
        self.diet_agent = DietAgent()
        self.activity_agent = ActivityAgent()
        self.behavior_agent = BehaviorAgent()

    def analyze_diary(self, text, callback=None):
        results = []

        diet_result = self.diet_agent.analyze(text)
        if callback: callback("DietAgent", diet_result)
        results.append(diet_result)

        activity_result = self.activity_agent.analyze(text)
        if callback: callback("ActivityAgent", activity_result)
        results.append(activity_result)

        behavior_result = self.behavior_agent.analyze(text)
        if callback: callback("BehaviorAgent", behavior_result)
        results.append(behavior_result)

        final_summary = "\n".join(results)
        if callback: callback("Summary", final_summary)
        return final_summary
