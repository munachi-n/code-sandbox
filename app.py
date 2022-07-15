from flask import Flask, request, jsonify
import os
import uuid

from executor import CodeExecutor, Sandbox, ExecutionHistory

app = Flask(__name__)

executor = CodeExecutor()
sandbox = Sandbox()
history = ExecutionHistory()

LANGUAGE_CONFIG = {
    "python": {"timeout": 5, "extensions": [".py"]},
    "javascript": {"timeout": 5, "extensions": [".js"]},
    "bash": {"timeout": 10, "extensions": [".sh"]},
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
    )


@app.route("/execute", methods=["POST"])
def execute_code():
    data = request.json

    code = data.get("code")
    language = data.get("language", "python")

    if not code:
        return jsonify({"error": "Code is required"}), 400

    if language not in executor.supported_languages:
        return jsonify({"error": f"Language {language} not supported"}), 400

    executor.timeout = data.get(
        "timeout", LANGUAGE_CONFIG.get(language, {}).get("timeout", 5)
    )

    result = executor.execute(code, language)

    history.add_execution(
        {
            "language": language,
            "code_length": len(code),
            "success": result["success"],
            "execution_time": result.get("execution_time"),
        }
    )

    return jsonify(result)


@app.route("/languages", methods=["GET"])
def get_languages():
    return jsonify(
        {"languages": executor.supported_languages, "config": LANGUAGE_CONFIG}
    )


@app.route("/sandboxes", methods=["POST"])
def create_sandbox():
    sandbox_id = request.json.get("sandbox_id")
    result = sandbox.create_sandbox(sandbox_id)
    return jsonify(result)


@app.route("/sandboxes", methods=["GET"])
def list_sandboxes():
    return jsonify({"sandboxes": sandbox.list_sandboxes()})


@app.route("/sandboxes/<sandbox_id>", methods=["DELETE"])
def delete_sandbox(sandbox_id):
    result = sandbox.delete_sandbox(sandbox_id)
    if result:
        return jsonify({"status": "deleted", "sandbox_id": sandbox_id})
    return jsonify({"error": "Sandbox not found"}), 404


@app.route("/history", methods=["GET"])
def get_history():
    limit = request.args.get("limit", 100, type=int)
    return jsonify({"history": history.get_history(limit)})


@app.route("/history", methods=["DELETE"])
def clear_history():
    history.clear_history()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
