"""
Rules Engine: 对话规则与拒绝规则引擎模块

本模块实现了基于关键词匹配的规则引擎，用于两类场景：
1. 对话规则（DEFAULT_RULES）：快速响应固定问题（帮助、版本、问候），
   跳过 LLM 推理，降低延迟和成本。
2. 拒绝规则（DEFAULT_REFUSAL_RULES）：拦截敏感内容（暴力、违法），
   在 LLM 处理前直接返回拒绝话术，保障内容安全。

规则匹配采用简单的关键词包含匹配（非正则），适合校园场景的有限词汇量。
长文本（>100 字符）自动跳过规则匹配，避免文件内容等大段文本误触发。
"""


# 默认对话规则列表
# 每条规则包含：name（规则名）、keywords（触发关键词列表）、response（固定回复）
# 匹配逻辑：用户输入包含任一关键词即命中，返回对应回复
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

# 默认拒绝规则列表
# 用于内容安全过滤，拦截涉及暴力、违法等敏感话题的输入
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
    """规则引擎实例

    管理对话规则和拒绝规则的增删查改。
    规则存储在内存列表中（非持久化），重启后恢复默认规则。
    如需持久化，可在后续版本中接入数据库。
    """

    def __init__(self):
        # 使用 copy() 避免修改默认列表的引用
        self.rules = DEFAULT_RULES.copy()
        self.refusal_rules = DEFAULT_REFUSAL_RULES.copy()

    def check_rules(self, query: str) -> str | None:
        """检查对话规则，返回匹配的回复或 None

        Args:
            query: 用户输入文本

        长文本（>100 字符）直接返回 None，因为：
        - 长文本通常是文件内容或粘贴的大段文字，不太可能匹配简短关键词
        - 避免误触发（如上传文档内容恰好包含"你好"）
        """
        query_lower = query.lower().strip()
        # 长文本跳过规则匹配，交给 LLM 处理
        if len(query_lower) > 100:
            return None
        for rule in self.rules:
            for kw in rule["keywords"]:
                if kw in query_lower:
                    return rule["response"]
        return None

    def check_refusal(self, query: str) -> str | None:
        """检查拒绝规则，返回拒绝话术或 None

        优先级高于对话规则和 LLM 推理——在对话流程中应最先调用。
        同样对长文本跳过匹配。
        """
        query_lower = query.lower().strip()
        if len(query_lower) > 100:
            return None
        for rule in self.refusal_rules:
            for kw in rule["keywords"]:
                if kw in query_lower:
                    return rule["response"]
        return None

    def add_rule(self, name: str, keywords: list[str], response: str):
        """添加对话规则（运行时生效，重启后丢失）"""
        self.rules.append({"name": name, "keywords": keywords, "response": response})

    def add_refusal_rule(self, name: str, keywords: list[str], response: str):
        """添加拒绝规则（运行时生效，重启后丢失）"""
        self.refusal_rules.append({"name": name, "keywords": keywords, "response": response})

    def remove_rule(self, name: str):
        """按名称删除对话规则"""
        self.rules = [r for r in self.rules if r["name"] != name]

    def remove_refusal_rule(self, name: str):
        """按名称删除拒绝规则"""
        self.refusal_rules = [r for r in self.refusal_rules if r["name"] != name]

    def get_rules(self) -> list[dict]:
        """获取所有对话规则"""
        return self.rules

    def get_refusal_rules(self) -> list[dict]:
        """获取所有拒绝规则"""
        return self.refusal_rules


# 模块级单例，供整个应用共享同一个规则引擎实例
rules_engine = RulesEngine()
