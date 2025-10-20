"""Flag and trivia guessing game with CLI and web interfaces."""
from __future__ import annotations

import argparse
import random
import sys
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from flask import Flask


INDEX_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Guess the Country</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: \"Inter\", \"Segoe UI\", system-ui, -apple-system, sans-serif;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0f172a, #1e293b);
      color: #e2e8f0;
      padding: 2rem;
    }

    .card {
      width: min(640px, 100%);
      background: rgba(15, 23, 42, 0.92);
      border-radius: 18px;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.55);
      padding: clamp(1.5rem, 2vw + 1rem, 2.5rem);
      border: 1px solid rgba(148, 163, 184, 0.15);
    }

    h1 {
      font-size: clamp(2rem, 3vw, 2.5rem);
      margin-top: 0;
      margin-bottom: 0.25rem;
      letter-spacing: 0.02em;
      text-align: center;
    }

    .tagline {
      text-align: center;
      margin: 0 0 1.5rem;
      color: #94a3b8;
    }

    .scoreboard {
      display: flex;
      justify-content: center;
      gap: 1.5rem;
      margin-bottom: 1.5rem;
      font-size: 1rem;
    }

    .scoreboard span {
      font-weight: 600;
      color: #f8fafc;
    }

    .clue-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 0.75rem;
    }

    .clue-list li {
      padding: 0.85rem 1rem;
      background: rgba(30, 41, 59, 0.85);
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      line-height: 1.4;
    }

    form {
      display: grid;
      gap: 1rem;
      margin-top: 1.5rem;
    }

    label {
      display: block;
      font-weight: 600;
      color: #cbd5f5;
    }

    input[type=\"text\"] {
      width: 100%;
      padding: 0.75rem 0.85rem;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.25);
      background: rgba(15, 23, 42, 0.7);
      color: inherit;
      font-size: 1rem;
      transition: border-color 0.2s ease;
    }

    input[type=\"text\"]:focus {
      outline: none;
      border-color: #38bdf8;
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      justify-content: space-between;
    }

    button {
      padding: 0.75rem 1.25rem;
      border: none;
      border-radius: 999px;
      cursor: pointer;
      font-weight: 600;
      letter-spacing: 0.01em;
      transition: transform 0.15s ease, box-shadow 0.2s ease;
    }

    button.primary {
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      color: #0f172a;
      box-shadow: 0 10px 20px rgba(56, 189, 248, 0.35);
    }

    button.secondary {
      background: rgba(148, 163, 184, 0.15);
      color: #e2e8f0;
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
      box-shadow: none !important;
    }

    button:not(:disabled):hover {
      transform: translateY(-1px);
      box-shadow: 0 14px 28px rgba(56, 189, 248, 0.35);
    }

    .status {
      margin-top: 1.5rem;
      padding: 0.85rem 1rem;
      border-radius: 12px;
      font-weight: 500;
      display: none;
    }

    .status.info {
      display: block;
      background: rgba(59, 130, 246, 0.2);
      border: 1px solid rgba(96, 165, 250, 0.35);
    }

    .status.success {
      display: block;
      background: rgba(34, 197, 94, 0.2);
      border: 1px solid rgba(34, 197, 94, 0.35);
    }

    .status.error {
      display: block;
      background: rgba(248, 113, 113, 0.2);
      border: 1px solid rgba(252, 165, 165, 0.35);
    }

    @media (max-width: 520px) {
      body {
        padding: 1.5rem;
      }

      .actions {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Guess the Country</h1>
    <p class=\"tagline\">Use the flag and trivia clues to figure out the answer.</p>

    <div class=\"scoreboard\" aria-live=\"polite\">
      <div>Score: <span id=\"score\">0</span></div>
      <div>Round: <span id=\"round\">1</span></div>
    </div>

    <ul id=\"clues\" class=\"clue-list\"></ul>

    <form id=\"guess-form\" autocomplete=\"off\">
      <div>
        <label for=\"guess\">Your Guess</label>
        <input id=\"guess\" name=\"guess\" type=\"text\" placeholder=\"Start typing a country...\" required />
      </div>
      <div class=\"actions\">
        <button type=\"submit\" class=\"primary\">Submit Guess</button>
        <button type=\"button\" id=\"next-clue\" class=\"secondary\">Reveal Next Clue</button>
        <button type=\"button\" id=\"new-game\" class=\"secondary\">Start New Game</button>
      </div>
    </form>

    <div id=\"status\" class=\"status\" role=\"status\" aria-live=\"polite\"></div>
  </div>

  <script>
    (() => {
      let gameId = null;
      let hasMoreClues = false;

      const clueList = document.getElementById("clues");
      const scoreEl = document.getElementById("score");
      const roundEl = document.getElementById("round");
      const statusEl = document.getElementById("status");
      const guessInput = document.getElementById("guess");
      const guessForm = document.getElementById("guess-form");
      const nextClueBtn = document.getElementById("next-clue");
      const newGameBtn = document.getElementById("new-game");

      const setStatus = (message, tone = "info") => {
        if (!message) {
          statusEl.style.display = "none";
          statusEl.textContent = "";
          statusEl.className = "status";
          return;
        }
        statusEl.className = `status ${tone}`;
        statusEl.textContent = message;
      };

      const updateScoreboard = (score, round) => {
        if (typeof score === "number") {
          scoreEl.textContent = String(score);
        }
        if (typeof round === "number") {
          roundEl.textContent = String(Math.max(1, round));
        }
      };

      const setClues = (clues) => {
        clueList.innerHTML = "";
        for (const clue of clues) {
          addClue(clue);
        }
      };

      const addClue = (clue) => {
        if (!clue) return;
        const item = document.createElement("li");
        item.textContent = clue;
        clueList.appendChild(item);
      };

      const setNextClueAvailability = (available) => {
        hasMoreClues = Boolean(available);
        nextClueBtn.disabled = !hasMoreClues;
      };

      const startGame = async () => {
        try {
          const response = await fetch("/api/new-game", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to start a new game.");
          }
          gameId = data.gameId;
          updateScoreboard(data.score ?? 0, data.round ?? 1);
          if (Array.isArray(data.clues)) {
            setClues(data.clues);
          } else {
            setClues([]);
            if (data.clue) {
              addClue(data.clue);
            }
          }
          setNextClueAvailability(data.hasMoreClues);
          setStatus("Game started! Enter a guess when you're ready.");
          guessInput.focus();
        } catch (error) {
          console.error(error);
          setStatus(error.message || "An unexpected error occurred.", "error");
        }
      };

      const requestNextClue = async () => {
        if (!gameId || !hasMoreClues) return;
        try {
          const response = await fetch("/api/next-clue", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gameId }),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "No additional clues available.");
          }
          addClue(data.clue);
          setNextClueAvailability(data.hasMoreClues);
          setStatus("Here's another clue!", "info");
          guessInput.focus();
        } catch (error) {
          console.error(error);
          setStatus(error.message || "Unable to fetch the next clue.", "error");
        }
      };

      const submitGuess = async () => {
        if (!gameId) return;
        const guess = guessInput.value.trim();
        if (!guess) {
          setStatus("Please enter a guess before submitting.", "error");
          return;
        }

        try {
          const response = await fetch("/api/guess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gameId, guess }),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to submit guess.");
          }

          if (data.correct) {
            setStatus(data.message || "Correct!", "success");
            updateScoreboard(data.score, data.round);
            setClues(data.nextClue ? [data.nextClue] : []);
            setNextClueAvailability(data.hasMoreClues);
            guessInput.value = "";
          } else if (data.hasMoreClues) {
            setStatus(data.message || "Not quite. Try the next clue.", "info");
          } else {
            setStatus(data.message || "Round complete!", "error");
            updateScoreboard(data.score, data.round);
            setClues(data.nextClue ? [data.nextClue] : []);
            setNextClueAvailability(data.hasMoreClues);
            guessInput.value = "";
          }

          guessInput.focus();
        } catch (error) {
          console.error(error);
          setStatus(error.message || "Unable to submit guess.", "error");
        }
      };

      guessForm.addEventListener("submit", (event) => {
        event.preventDefault();
        submitGuess();
      });

      nextClueBtn.addEventListener("click", requestNextClue);
      newGameBtn.addEventListener("click", () => {
        setStatus("Starting a fresh game...");
        startGame();
      });

      startGame();
    })();
  </script>
</body>
</html>
"""


@dataclass(frozen=True)
class CountryClue:
    """A single country's trivia and flag clues."""

    name: str
    flag: str
    hints: Sequence[str]

    def normalized_name(self) -> str:
        """Return the normalized name used for comparisons."""

        return self.name.strip().lower()


COUNTRY_DATA: List[CountryClue] = [
    CountryClue(
        name="Canada",
        flag="🇨🇦",
        hints=(
            "The capital city is Ottawa.",
            "This country is famous for maple syrup and ice hockey.",
            "It has the longest coastline in the world.",
        ),
    ),
    CountryClue(
        name="Japan",
        flag="🇯🇵",
        hints=(
            "Its flag is a white field with a red circle in the center.",
            "The capital city is Tokyo.",
            "Home to Mount Fuji and a bullet-train network.",
        ),
    ),
    CountryClue(
        name="Brazil",
        flag="🇧🇷",
        hints=(
            "This country hosts part of the Amazon rainforest.",
            "Its official language is Portuguese.",
            "The city of Rio de Janeiro is famous for Carnival.",
        ),
    ),
    CountryClue(
        name="Kenya",
        flag="🇰🇪",
        hints=(
            "Located on the equator in East Africa.",
            "The Great Rift Valley runs through this country.",
            "It is renowned for long-distance runners.",
        ),
    ),
    CountryClue(
        name="Australia",
        flag="🇦🇺",
        hints=(
            "This country's flag includes the Union Jack and the Southern Cross.",
            "The capital city is Canberra.",
            "Home to the Great Barrier Reef.",
        ),
    ),
    CountryClue(
        name="Germany",
        flag="🇩🇪",
        hints=(
            "Its flag consists of horizontal stripes of black, red, and gold.",
            "The capital city is Berlin.",
            "Known for Oktoberfest and the Autobahn.",
        ),
    ),
    CountryClue(
        name="India",
        flag="🇮🇳",
        hints=(
            "Its flag has saffron, white, and green horizontal stripes with a navy blue wheel.",
            "The capital city is New Delhi.",
            "The Taj Mahal is one of its most famous landmarks.",
        ),
    ),
    CountryClue(
        name="Mexico",
        flag="🇲🇽",
        hints=(
            "Its flag features green, white, and red vertical stripes with an eagle emblem.",
            "The capital city shares the country's name.",
            "Known for cuisine featuring corn, beans, and chili peppers.",
        ),
    ),
    CountryClue(
        name="Norway",
        flag="🇳🇴",
        hints=(
            "This country's flag is a red field with a blue cross outlined in white.",
            "It has famous fjords carved by glaciers.",
            "The capital city is Oslo.",
        ),
    ),
    CountryClue(
        name="Argentina",
        flag="🇦🇷",
        hints=(
            "Its flag is light blue and white with a golden sun.",
            "The capital city is Buenos Aires.",
            "Home of the tango and renowned for beef.",
        ),
    ),
]


def normalize_guess(guess: str) -> str:
    """Normalize user guesses for comparison."""

    return guess.strip().lower()


def iter_clues(clue: CountryClue) -> Iterable[str]:
    """Yield the clues for a country in the order they should be shown."""

    yield f"Flag: {clue.flag}"
    for hint in clue.hints:
        yield hint


@dataclass
class GameSession:
    """State container for a single web session."""

    rng: random.Random
    score: int = 0
    round_number: int = 0
    current_clue: CountryClue | None = None
    clues: List[str] = field(default_factory=list)
    clue_index: int = 0

    def start_new_round(self) -> None:
        """Select a new country and reset clue progression."""

        if not COUNTRY_DATA:
            raise ValueError("No country data available.")
        self.current_clue = self.rng.choice(COUNTRY_DATA)
        self.clues = list(iter_clues(self.current_clue))
        self.clue_index = 0
        self.round_number += 1

    def reveal_next_clue(self) -> str | None:
        """Reveal and return the next clue, if available."""

        if self.current_clue is None or self.clue_index >= len(self.clues):
            return None
        clue = self.clues[self.clue_index]
        self.clue_index += 1
        return clue

    def has_more_clues(self) -> bool:
        """Return True when the current round has more unrevealed clues."""

        return self.current_clue is not None and self.clue_index < len(self.clues)

    def current_answer(self) -> str:
        """Return the answer for the active round."""

        if self.current_clue is None:
            raise ValueError("No active round.")
        return self.current_clue.name

    def check_guess(self, guess: str) -> bool:
        """Check whether a guess matches the current country."""

        if self.current_clue is None:
            raise ValueError("No active round.")
        return normalize_guess(guess) == self.current_clue.normalized_name()


def play_round(rng: random.Random, clue: CountryClue) -> bool:
    """Play a single round; return True if the player guessed correctly."""

    print("\n----------------------------------------")
    print("Guess the country!")
    for attempt, clue_text in enumerate(iter_clues(clue), start=1):
        print(f"\nClue {attempt}: {clue_text}")
        guess = input("Your guess (or type 'quit' to exit): ")
        normalized = normalize_guess(guess)
        if not normalized:
            print("Please enter a guess or type 'quit' to stop playing.")
            continue
        if normalized in {"quit", "exit", "q"}:
            raise KeyboardInterrupt
        if normalized == clue.normalized_name():
            print("Correct! 🎉")
            return True
        print("Not quite. Try another clue!")

    print(f"Out of clues! The correct answer was {clue.name}.")
    return False


def play_game(rounds: int | None = None, seed: int | None = None) -> None:
    """Run the main gameplay loop."""

    if not COUNTRY_DATA:
        print("No country data available. Please extend COUNTRY_DATA and try again.")
        return

    rng = random.Random(seed)
    total_rounds = 0
    score = 0

    print("Welcome to Guess the Country!")
    print("Try to identify the country using the flag and hints provided.")
    print("Type 'quit' at any time to exit the game.")

    try:
        while True:
            if rounds is not None and rounds > 0 and total_rounds >= rounds:
                break
            clue = rng.choice(COUNTRY_DATA)
            total_rounds += 1
            if play_round(rng, clue):
                score += 1
    except KeyboardInterrupt:
        print("\nThanks for playing!")
    finally:
        if total_rounds:
            print(
                f"\nFinal score: {score} correct out of {total_rounds} round{'s' if total_rounds != 1 else ''}."
            )
        else:
            print("No rounds played this session.")


def create_app(*, seed: int | None = None) -> "Flask":
    """Create and configure the Flask application for the web UI."""

    from flask import Flask, jsonify, render_template_string, request

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    games: Dict[str, GameSession] = {}
    lock = threading.Lock()
    base_rng = random.Random(seed)

    def make_session(session_seed: int | None = None) -> GameSession:
        rng = random.Random(session_seed) if session_seed is not None else random.Random(base_rng.random())
        session = GameSession(rng=rng)
        session.start_new_round()
        return session

    @app.get("/")
    def index() -> str:
        return render_template_string(INDEX_HTML)

    @app.post("/api/new-game")
    def api_new_game():  # type: ignore[override]
        payload = request.get_json(silent=True) or {}
        session_seed = payload.get("seed")

        try:
            session = make_session(session_seed)
        except ValueError as exc:  # no country data
            return jsonify({"error": str(exc)}), 503

        game_id = uuid.uuid4().hex
        first_clue = session.reveal_next_clue()
        with lock:
            games[game_id] = session

        return (
            jsonify(
                {
                    "gameId": game_id,
                    "round": session.round_number,
                    "score": session.score,
                    "clue": first_clue,
                    "hasMoreClues": session.has_more_clues(),
                }
            ),
            200,
        )

    def get_session(game_id: str | None) -> GameSession:
        if not game_id:
            raise KeyError("gameId is required.")
        session = games.get(game_id)
        if session is None:
            raise LookupError("Game not found.")
        return session

    @app.post("/api/next-clue")
    def api_next_clue():  # type: ignore[override]
        payload = request.get_json(silent=True) or {}
        try:
            with lock:
                session = get_session(payload.get("gameId"))
                clue = session.reveal_next_clue()
                if clue is None:
                    return jsonify({"error": "No more clues available."}), 409
                has_more = session.has_more_clues()
                round_number = session.round_number
        except KeyError as exc:
            return jsonify({"error": str(exc)}), 400
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404

        return (
            jsonify(
                {
                    "clue": clue,
                    "hasMoreClues": has_more,
                    "round": round_number,
                }
            ),
            200,
        )

    @app.post("/api/guess")
    def api_guess():  # type: ignore[override]
        payload = request.get_json(silent=True) or {}
        guess = normalize_guess(payload.get("guess", ""))
        if not guess:
            return jsonify({"error": "Please provide a guess."}), 400

        try:
            with lock:
                session = get_session(payload.get("gameId"))
                answer = session.current_answer()
                current_round = session.round_number

                if session.check_guess(guess):
                    session.score += 1
                    try:
                        session.start_new_round()
                        next_clue = session.reveal_next_clue()
                    except ValueError as exc:
                        return jsonify({"error": str(exc)}), 503

                    response = {
                        "correct": True,
                        "message": f"Correct! The answer was {answer}.",
                        "score": session.score,
                        "completedRound": current_round,
                        "round": session.round_number,
                        "nextClue": next_clue,
                        "hasMoreClues": session.has_more_clues(),
                    }
                else:
                    if session.has_more_clues():
                        response = {
                            "correct": False,
                            "message": "Not quite. Here's another clue!",
                            "hasMoreClues": True,
                            "round": current_round,
                            "score": session.score,
                        }
                    else:
                        try:
                            session.start_new_round()
                            next_clue = session.reveal_next_clue()
                        except ValueError as exc:
                            return jsonify({"error": str(exc)}), 503

                        response = {
                            "correct": False,
                            "message": f"Out of clues! The correct answer was {answer}.",
                            "answer": answer,
                            "score": session.score,
                            "completedRound": current_round,
                            "round": session.round_number,
                            "nextClue": next_clue,
                            "hasMoreClues": session.has_more_clues(),
                        }
        except KeyError as exc:
            return jsonify({"error": str(exc)}), 400
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404

        return jsonify(response)

    return app


def run_web_app(host: str = "127.0.0.1", port: int = 5000, *, seed: int | None = None) -> None:
    """Convenience helper to run the Flask development server."""

    try:
        app = create_app(seed=seed)
    except ImportError as exc:  # pragma: no cover - requires Flask
        raise RuntimeError("Flask is required to run the web interface.") from exc
    app.run(host=host, port=port, debug=False)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the game."""

    parser = argparse.ArgumentParser(description="Play the Guess the Country flag game.")
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Number of rounds to play. If omitted, play until you choose to quit.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible clue ordering.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the realtime web interface instead of the CLI.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the game with command-line arguments."""

    args = parse_args(argv)
    if args.web:
        run_web_app(seed=args.seed)
        return 0

    try:
        play_game(rounds=args.rounds, seed=args.seed)
    except KeyboardInterrupt:
        print("\nExiting game at your request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
