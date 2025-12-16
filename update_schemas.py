path = r"d:\rag-on-premise\backend\api\models\schemas.py"
with open(path, "r") as f:
    content = f.read()

new_content = content.replace(
    '    status: str',
    '    status: str\n    valid_questions: Optional[List[str]] = None'
)

with open(path, "w") as f:
    f.write(new_content)
