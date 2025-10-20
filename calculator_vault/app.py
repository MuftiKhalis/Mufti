"""Flask application that combines a feature-rich calculator with a secure vault."""
from __future__ import annotations

import ast
import base64
import datetime as dt
import hashlib
import math
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request, session

try:
    from cryptography.fernet import Fernet
except ImportError as exc:  # pragma: no cover - dependency error surface early
    raise SystemExit(
        "cryptography is required for calculator vault encryption."
    ) from exc


APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = APP_ROOT.parent / "data"
DB_PATH = DATA_DIR / "calculator_vault.sqlite"
DATA_DIR.mkdir(exist_ok=True)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.setdefault(
        "SECRET_KEY",
        os.environ.get("CALCULATOR_VAULT_SECRET_KEY", "dev-secret-key"),
    )
    init_db()

    @app.route("/")
    def index() -> str:
        return render_template("calculator_vault.html")

    @app.post("/api/calc")
    def calculate() -> Any:
        data = request.get_json(silent=True) or {}
        expression = (data.get("expression") or "").strip()
        if not expression:
            return jsonify({"error": "Expression is required."}), 400
        try:
            result = evaluate_expression(expression)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        record_history(expression, result)
        return jsonify({"result": result})

    @app.get("/api/history")
    def get_history() -> Any:
        return jsonify({"history": fetch_history()})

    @app.delete("/api/history/<int:history_id>")
    def delete_history(history_id: int) -> Any:
        with db_connection() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (history_id,))
            conn.commit()
        return "", 204

    @app.delete("/api/history")
    def clear_history() -> Any:
        with db_connection() as conn:
            conn.execute("DELETE FROM history")
            conn.commit()
        return "", 204

    @app.get("/api/vault/status")
    def vault_status() -> Any:
        settings = fetch_vault_settings()
        unlocked = "vault_key" in session
        return jsonify(
            {
                "configured": settings is not None,
                "unlocked": unlocked,
            }
        )

    @app.post("/api/vault/setup")
    def vault_setup() -> Any:
        if fetch_vault_settings() is not None:
            return jsonify({"error": "Vault is already configured."}), 400
        payload = request.get_json(silent=True) or {}
        password = (payload.get("password") or "").strip()
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters."}), 400
        store_master_password(password)
        session["vault_key"] = derive_session_key(password)
        session.modified = True
        return jsonify({"message": "Vault configured successfully."}), 201

    @app.post("/api/vault/unlock")
    def vault_unlock() -> Any:
        settings = fetch_vault_settings()
        if settings is None:
            return jsonify({"error": "Vault has not been configured yet."}), 400
        payload = request.get_json(silent=True) or {}
        password = (payload.get("password") or "").strip()
        if not password:
            return jsonify({"error": "Password is required."}), 400
        if not verify_master_password(password, settings):
            return jsonify({"error": "Incorrect password."}), 403
        session["vault_key"] = derive_session_key(password, settings["salt"])
        session.modified = True
        return jsonify({"message": "Vault unlocked."})

    @app.post("/api/vault/lock")
    def vault_lock() -> Any:
        session.pop("vault_key", None)
        return jsonify({"message": "Vault locked."})

    @app.get("/api/vault/entries")
    def vault_entries() -> Any:
        fernet = session_fernet()
        if fernet is None:
            return jsonify({"error": "Vault is locked."}), 403
        entries = []
        with db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, title, ciphertext, created_at, updated_at FROM vault_entries"
                " ORDER BY created_at DESC"
            )
            for row in cursor.fetchall():
                try:
                    content = fernet.decrypt(row[2]).decode("utf-8")
                except Exception:  # pragma: no cover - corrupt data guard
                    content = "<Unable to decrypt entry>"
                entries.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "content": content,
                        "created_at": row[3],
                        "updated_at": row[4],
                    }
                )
        return jsonify({"entries": entries})

    @app.post("/api/vault/entries")
    def vault_create_entry() -> Any:
        fernet = session_fernet()
        if fernet is None:
            return jsonify({"error": "Vault is locked."}), 403
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        content = (payload.get("content") or "").strip()
        if not title or not content:
            return jsonify({"error": "Title and content are required."}), 400
        ciphertext = fernet.encrypt(content.encode("utf-8"))
        now = dt.datetime.utcnow().isoformat()
        with db_connection() as conn:
            conn.execute(
                "INSERT INTO vault_entries(title, ciphertext, created_at, updated_at)"
                " VALUES(?, ?, ?, ?)",
                (title, ciphertext, now, now),
            )
            conn.commit()
        return jsonify({"message": "Entry saved."}), 201

    @app.put("/api/vault/entries/<int:entry_id>")
    def vault_update_entry(entry_id: int) -> Any:
        fernet = session_fernet()
        if fernet is None:
            return jsonify({"error": "Vault is locked."}), 403
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        content = (payload.get("content") or "").strip()
        if not title or not content:
            return jsonify({"error": "Title and content are required."}), 400
        ciphertext = fernet.encrypt(content.encode("utf-8"))
        now = dt.datetime.utcnow().isoformat()
        with db_connection() as conn:
            conn.execute(
                "UPDATE vault_entries SET title = ?, ciphertext = ?, updated_at = ?"
                " WHERE id = ?",
                (title, ciphertext, now, entry_id),
            )
            conn.commit()
        return jsonify({"message": "Entry updated."})

    @app.delete("/api/vault/entries/<int:entry_id>")
    def vault_delete_entry(entry_id: int) -> Any:
        fernet = session_fernet()
        if fernet is None:
            return jsonify({"error": "Vault is locked."}), 403
        with db_connection() as conn:
            conn.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))
            conn.commit()
        return "", 204

    @app.get("/healthz")
    def healthcheck() -> Any:
        return jsonify({"status": "ok"})

    return app


def init_db() -> None:
    with db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS vault_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                salt BLOB NOT NULL,
                password_hash BLOB NOT NULL
            );

            CREATE TABLE IF NOT EXISTS vault_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ciphertext BLOB NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


ALLOWED_NAMES: Dict[str, Any] = {
    name: getattr(math, name)
    for name in (
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "sqrt",
        "log",
        "log10",
        "exp",
        "pow",
        "pi",
        "e",
        "factorial",
        "degrees",
        "radians",
        "sinh",
        "cosh",
        "tanh",
        "floor",
        "ceil",
        "gamma",
    )
}
ALLOWED_NAMES.update({"abs": abs, "round": round})


class ExpressionEvaluator(ast.NodeVisitor):
    """Safely evaluate mathematical expressions using the AST module."""

    def visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Num):  # pragma: no cover - python <3.8 compat
            return node.n
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid constant in expression")
        if isinstance(node, ast.BinOp):
            return self._eval_binop(node)
        if isinstance(node, ast.UnaryOp):
            return self._eval_unary(node)
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        if isinstance(node, ast.Name):
            if node.id in ALLOWED_NAMES:
                return ALLOWED_NAMES[node.id]
            raise ValueError(f"Use of '{node.id}' is not allowed")
        if isinstance(node, ast.Expr):
            return self.visit(node.value)
        raise ValueError("Unsupported expression")

    def _eval_binop(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left ** right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        raise ValueError("Unsupported binary operation")

    def _eval_unary(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            raise ValueError("Logical not is not supported")
        raise ValueError("Unsupported unary operation")

    def _eval_call(self, node: ast.Call) -> Any:
        func = self.visit(node.func)
        if func not in ALLOWED_NAMES.values():
            raise ValueError("Function is not allowed")
        args = [self.visit(arg) for arg in node.args]
        return func(*args)


def evaluate_expression(expression: str) -> str:
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - parse errors bubble up
        raise ValueError("Invalid expression") from exc
    evaluator = ExpressionEvaluator()
    value = evaluator.visit(parsed)
    if isinstance(value, float):
        value = round(value, 10)
        formatted = f"{value:.10f}".rstrip("0").rstrip(".")
        return formatted or "0"
    if isinstance(value, int):
        return str(value)
    raise ValueError("Expression did not produce a numeric result")


def record_history(expression: str, result: str) -> None:
    with db_connection() as conn:
        conn.execute(
            "INSERT INTO history(expression, result, created_at) VALUES(?, ?, ?)",
            (expression, result, dt.datetime.utcnow().isoformat()),
        )
        conn.commit()


def fetch_history() -> Any:
    with db_connection() as conn:
        cursor = conn.execute(
            "SELECT id, expression, result, created_at FROM history ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]


def store_master_password(password: str) -> None:
    salt = os.urandom(16)
    password_hash = _derive_raw_key(password, salt)
    with db_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO vault_settings(id, salt, password_hash) VALUES(1, ?, ?)",
            (salt, password_hash),
        )
        conn.commit()


def fetch_vault_settings() -> Dict[str, Any] | None:
    with db_connection() as conn:
        cursor = conn.execute("SELECT salt, password_hash FROM vault_settings WHERE id = 1")
        row = cursor.fetchone()
        if row is None:
            return None
        return {"salt": row[0], "password_hash": row[1]}


def verify_master_password(password: str, settings: Dict[str, Any]) -> bool:
    candidate = _derive_raw_key(password, settings["salt"])
    return secrets_compare(candidate, settings["password_hash"])


def derive_session_key(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        settings = fetch_vault_settings()
        salt = settings["salt"] if settings else os.urandom(16)
    raw_key = _derive_raw_key(password, salt)
    return base64.urlsafe_b64encode(raw_key).decode("utf-8")


def session_fernet() -> Fernet | None:
    token = session.get("vault_key")
    if not token:
        return None
    return Fernet(token.encode("utf-8"))


def _derive_raw_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 390000, dklen=32)


def secrets_compare(value: bytes, expected: bytes) -> bool:
    if len(value) != len(expected):
        return False
    result = 0
    for x, y in zip(value, expected):
        result |= x ^ y
    return result == 0


def main() -> None:
    app = create_app()
    app.run(debug=True)


if __name__ == "__main__":  # pragma: no cover
    main()
