"""LLM + AST code migration engine."""
import ast
from langchain_google_vertexai import ChatVertexAI
from pathlib import Path
from typing import Dict

MIGRATION_RULES = {
    "python2_to_3": [
        "Convert print statements to print() functions",
        "Change .iteritems() to .items(), .itervalues() to .values()",
        "Convert unicode() to str(), basestring to str",
        "Fix integer division // where needed",
        "Update except Exception, e to except Exception as e",
        "Replace xrange with range"
    ],
    "pandas_legacy": [
        "Replace .append() with pd.concat()",
        "Replace .iteritems() with .items()",
        "Replace inplace=True where deprecated",
        "Update .ix[] to .loc[] or .iloc[]",
        "Fix chained assignment warnings"
    ],
    "sklearn_legacy": [
        "Update class_weight parameter names",
        "Fix n_jobs default changes",
        "Update predict_proba for multi-output",
        "Replace deprecated transform patterns"
    ]
}

class CodeMigrator:
    def __init__(self):
        self.llm = ChatVertexAI(model_name="gemini-1.5-pro-002", temperature=0)

    def migrate(self, source_code: str, migration_type: str) -> Dict:
        rules = MIGRATION_RULES.get(migration_type, [])
        rules_str = "\n".join(f"- {r}" for r in rules)
        prompt = f"""Migrate this code ({migration_type} migration). Apply ALL rules:
{rules_str}

Source code:
```python
{source_code}
```

Return ONLY the migrated Python code, no explanations, no markdown."""
        migrated = self.llm.invoke(prompt).content
        if "```python" in migrated: migrated = migrated.split("```python")[1].split("```")[0]
        # Validate syntax
        syntax_ok = True
        try: ast.parse(migrated)
        except SyntaxError as e: syntax_ok = False
        return {"migrated_code": migrated.strip(), "syntax_valid": syntax_ok,
                "migration_type": migration_type, "lines_original": len(source_code.splitlines()),
                "lines_migrated": len(migrated.splitlines())}

    def migrate_file(self, file_path: str, migration_type: str, backup: bool = True) -> Dict:
        source = Path(file_path).read_text(encoding="utf-8")
        if backup: Path(file_path + ".bak").write_text(source)
        result = self.migrate(source, migration_type)
        if result["syntax_valid"]:
            Path(file_path).write_text(result["migrated_code"], encoding="utf-8")
        return result
