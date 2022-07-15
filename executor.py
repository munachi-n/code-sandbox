import subprocess
import tempfile
import os
import uuid
import time
import json
from datetime import datetime


class CodeExecutor:
    def __init__(self, timeout=5, max_memory_mb=128):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.supported_languages = ["python", "javascript", "bash"]

    def execute(self, code, language="python"):
        if language not in self.supported_languages:
            return {"success": False, "error": f"Language {language} not supported"}

        execution_id = str(uuid.uuid4())[:8]

        with tempfile.TemporaryDirectory() as tmpdir:
            if language == "python":
                filepath = os.path.join(tmpdir, f"script_{execution_id}.py")
            elif language == "javascript":
                filepath = os.path.join(tmpdir, f"script_{execution_id}.js")
            elif language == "bash":
                filepath = os.path.join(tmpdir, f"script_{execution_id}.sh")

            with open(filepath, "w") as f:
                f.write(code)

            try:
                start_time = time.time()

                result = subprocess.run(
                    [
                        "python"
                        if language == "python"
                        else ("node" if language == "javascript" else "bash"),
                        filepath,
                    ],
                    capture_output=True,
                    timeout=self.timeout,
                    text=True,
                )

                elapsed_time = time.time() - start_time

                return {
                    "success": True,
                    "output": result.stdout,
                    "error": result.stderr if result.stderr else None,
                    "exit_code": result.returncode,
                    "execution_time": round(elapsed_time, 3),
                    "execution_id": execution_id,
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Execution timed out after {self.timeout} seconds",
                    "execution_id": execution_id,
                }
            except Exception as e:
                return {"success": False, "error": str(e), "execution_id": execution_id}


class Sandbox:
    def __init__(self, base_dir="sandboxes"):
        self.base_dir = base_dir
        self.executor = CodeExecutor()
        os.makedirs(base_dir, exist_ok=True)

    def create_sandbox(self, sandbox_id=None):
        if sandbox_id is None:
            sandbox_id = str(uuid.uuid4())[:12]

        sandbox_path = os.path.join(self.base_dir, sandbox_id)
        os.makedirs(sandbox_path, exist_ok=True)

        return {
            "sandbox_id": sandbox_id,
            "path": sandbox_path,
            "created_at": datetime.now().isoformat(),
        }

    def delete_sandbox(self, sandbox_id):
        sandbox_path = os.path.join(self.base_dir, sandbox_id)
        if os.path.exists(sandbox_path):
            import shutil

            shutil.rmtree(sandbox_path)
            return True
        return False

    def list_sandboxes(self):
        sandboxes = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path):
                sandboxes.append(
                    {
                        "sandbox_id": item,
                        "path": item_path,
                        "created_at": datetime.fromtimestamp(
                            os.path.getctime(item_path)
                        ).isoformat(),
                    }
                )
        return sandboxes


class ExecutionHistory:
    def __init__(self, storage_file="execution_history.json"):
        self.storage_file = storage_file
        self.history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r") as f:
                return json.load(f)
        return []

    def _save_history(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def add_execution(self, execution_data):
        self.history.append({"timestamp": datetime.now().isoformat(), **execution_data})
        self._save_history()

    def get_history(self, limit=100):
        return self.history[-limit:]

    def clear_history(self):
        self.history = []
        self._save_history()


if __name__ == "__main__":
    executor = CodeExecutor()

    result = executor.execute('print("Hello, World!")', "python")
    print(result)
