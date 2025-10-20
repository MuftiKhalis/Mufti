# Guess the Country

An interactive geography quiz that challenges you to identify countries
from their flags and trivia clues. The game runs entirely in the
terminal and is powered by a structured dataset of countries defined in
[`game/guess_the_country.py`](game/guess_the_country.py).

## Getting Started

1. Ensure you have Python 3.9 or newer installed.
2. Clone this repository and open a terminal in the project root.
3. Run the game with:

   ```bash
   python -m game.guess_the_country
   ```

   Optional arguments:

   - `--rounds N` limits the session to `N` rounds (otherwise the game
     continues until you type `quit`).
   - `--seed SEED` sets a deterministic random seed, which is useful for
     demonstrations or testing.

Press `Ctrl+C`, type `quit`, or enter `exit` at any guess prompt to end
the session. After each round the game reports whether you guessed the
country correctly and keeps a running score.

## Extending the Dataset

Country data lives in the `COUNTRY_DATA` list within
[`game/guess_the_country.py`](game/guess_the_country.py). Each entry is a
`CountryClue` instance with a country name, flag emoji, and a collection
of textual hints.

To add more countries:

1. Open `game/guess_the_country.py`.
2. Append a new `CountryClue` to `COUNTRY_DATA`, providing:
   - `name`: The country's common name (e.g., `"Spain"`).
   - `flag`: A Unicode flag emoji or simple ASCII description.
   - `hints`: A tuple of one or more textual hints that become
     progressively more revealing.
3. Save the file and rerun the game.

The hints appear sequentially after each incorrect guess, so arrange
them from most cryptic to most informative to balance difficulty.

## Original Profile README

- 👋 Hi, I’m @MuftiKhalis
- 👀 I’m interested in tech
- 🌱 I’m currently learning biological sciences
- 💞️ I’m looking to collaborate on nothing
- 📫 How to reach me ...

<!---
MuftiKhalis/MuftiKhalis is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
-->
