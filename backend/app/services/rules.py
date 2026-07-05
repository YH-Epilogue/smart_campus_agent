"""
Rules Engine: 对话规则配置 + 拒绝回答配置
"""
import re


# 默认对话规则
DEFAULT_RULES = [
    {
        "name": "帮助",
        "keywords": ["帮助", "怎么用", "使用方法", "功能"],
        "response": "Smart Campus Agent 功能：\n1. 知识库问答 - 基于上传的文档回答问题\n2. 多轮对话 - 支持上下文追问\n3. 快捷提问 - 点击预设问题快速提问",
    },
    {
        "name": "版本",
        "keywords": ["版本", "version"],
        "response": "Smart Campus Agent v0.1.0\n基于 RAG 技术的校园智能问答平台",
    },
    {
        "name": "问候",
        "keywords": ["你好", "您好", "hi", "hello", "嗨"],
        "response": "你好！我是 Smart Campus Agent，有什么可以帮你的吗？",
    },
]

# 默认拒绝规则
DEFAULT_REFUSAL_RULES = [
    {
        "name": "暴力内容",
        "keywords": ["杀人", "爆炸", "武器", "攻击"],
        "response": "抱歉，我无法回答涉及暴力或危险行为的问题。",
    },
    {
        "name": "违法内容",
        "keywords": ["毒品", "赌博", "诈骗", "盗窃"],
        "response": "抱歉，我无法回答涉及违法活动的问题。",
    },
]


class RulesEngine:
    def __init__(self):
        self.rules = DEFAULT_RULES.copy()
        self.refusal_rules = DEFAULT_REFUSAL_RULES.copy()

    def check_rules(self, query: str) -> str | None:
        """检查对话规则，返回匹配的回复或 None"""
        query_lower = query.lower().strip()
        # Skip rule matching for long queries (likely file content)
        if len(query_lower) > 100:
            return None
        for rule in self.rules:
            for kw in rule["keywords"]:
                if kw in query_lower:
                    return rule["response"]
        return None

    def check_refusal(self, query: str) -> str | None:
        """检查拒绝规则，返回拒绝话术或 None"""
        query_lower = query.lower().strip()
        if len(query_lower) > 100:
            return None
        for rule in self.refusal_rules:
            for kw in rule["keywords"]:
                if kw in query_lower:
                    return rule["response"]
        return None

    def add_rule(self, name: str, keywords: list[str], response: str):
        """添加对话规则"""
        self.rules.append({"name": name, "keywords": keywords, "response": response})

    def add_refusal_rule(self, name: str, keywords: list[str], response: str):
        """添加拒绝规则"""
        self.refusal_rules.append({"name": name, "keywords": keywords, "response": response})

    def remove_rule(self, name: str):
        """删除对话规则"""
        self.rules = [r for r in self.rules if r["name"] != name]

    def remove_refusal_rule(self, name: str):
        """删除拒绝规则"""
        self.refusal_rules = [r for r in self.refusal_rules if r["name"] != name]

    def get_rules(self) -> list[dict]:
        """获取所有对话规则"""
        return self.rules

    def get_refusal_rules(self) -> list[dict]:
        """获取所有拒绝规则"""
        return self.refusal_rules


rules_engine = RulesEngine()
