from src.strategies.base import MiningStrategy
from src.models import ArgumentGraph
from src.llm import LLMClient

class IBISStrategy(MiningStrategy):
    def analyze(self, text: str) -> ArgumentGraph:
        llm = LLMClient()
        
        # プロンプトを日本語指示向けに調整
        system_prompt = """
あなたは議論構造化のプロフェッショナルです。IBISモデルに基づいて会話ログを構造化してください。

# Definitions (ノードの定義)
- **issue**: 議論の論点や問い (Shape: Circle)
- **position**: 問いに対する提案や意見 (Shape: Rect)
- **argument**: 提案に対する根拠・支持・懸念 (Shape: Tag)
- **decision**: 最終的な決定事項 (Shape: Hexagon)

# Rules (抽出ルール)
1. 会話から主要なIssue(論点)を特定する。
2. それに対するPosition(提案)を特定する。
3. Argument(根拠)を特定し、支持か反対かを明確にする。
4. 結論が出ている場合はDecision(決定)とする。
5. **出力する `content` は簡潔な日本語の要約にすること。**
6. **各ノードには、会話ログにおける出現順を示す `sequence` (1から始まる整数) を必ず付与すること。**

# Edge Labels (矢印のラベル定義)
以下の日本語ラベルを使用してください：
- Position -> **提案** -> Issue
- Argument -> **支持** -> Position (肯定的な理由)
- Argument -> **懸念** -> Position (否定的な理由・反対意見)
- Decision -> **決定** -> Position (採用された案)

# Output Format (JSON)
Strictly output in JSON format matching this schema:
{
  "nodes": [
    {"id": "n1", "type": "issue", "content": "使用言語はどうするか？", "speaker": "田中", "sequence": 1},
    {"id": "n2", "type": "position", "content": "Pythonを採用する", "speaker": "佐藤", "sequence": 2}
  ],
  "edges": [
    {"source": "n2", "target": "n1", "label": "提案"}
  ]
}
Note: `type` must be strictly one of: "issue", "position", "argument", "decision".
"""
        # LLMを実行
        data = llm.fetch_json(system_prompt, text)
        
        # Pydanticモデルに変換
        return ArgumentGraph(**data)