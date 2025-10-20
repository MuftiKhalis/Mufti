"""Command-line geography quiz game focused on world flags.

This module exposes a ``main`` entry point that launches an
interactive guessing game. The structured data source for the game is
``COUNTRY_DATA`` which contains country names and related flag clues.
"""
from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from typing import Iterable, List, Sequence


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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the game with command-line arguments."""

    args = parse_args(argv)
    try:
        play_game(rounds=args.rounds, seed=args.seed)
    except KeyboardInterrupt:
        print("\nExiting game at your request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
