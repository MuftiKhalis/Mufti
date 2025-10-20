from __future__ import annotations

from flask import Flask, render_template


def create_app() -> Flask:
    """Application factory for the planning and invoicing dashboard."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    @app.route("/")
    def index() -> str:
        """Serve the real-time planning and invoicing workspace."""
        return render_template("index.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
