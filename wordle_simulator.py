"""
This scripts tests the algorithm performance in normal and hard mode.

It's currently configured to run off the 12Dict list.
"""
#%%
import pickle
from collections import Counter
from wordle import WordleInformation, rank_guesses, make_guess
from word_lists import (
    twelve_dict_words,
    twelve_dict_weights,
    wordle_guesses,
    wordle_weights,
    wordle_answers,
)


def play_game(
    answer, initial_guess, possible_words, weights=None, verbose=False, hard_mode=False
):
    """
    Plays a game of Wordle.

    :param answer: The answer
    :param initial_guess: The initial guess to make.
    :param possible_words: The possible words list.
    :param weights: The weights for the possible words list.
    :param verbose: If True, output text to show teh game progress.
    :param hard_mode: If True, then play Wordle in Hard mode. In this mode, the
        guess must match the game information so far.

    :returns: The number of rounds to win. 7 if the computer didn't win in six
        rounds. 8 if the word isn't in the list.
    """
    if verbose:
        print(f"Starting game for '{answer}'")
    if answer not in possible_words:
        print(f"Game impossible for {answer} with word list.")
        return 8
    wi = WordleInformation()
    possible_solutions = tuple(possible_words)
    possible_words = tuple(possible_words)  # Lose the reference.
    guess = initial_guess
    won_game = False
    guess_count = 0

    while True:
        # Make the guess and update the information
        out = make_guess(guess, answer)
        wi = WordleInformation(wi, guess, out)
        guess_count += 1

        # Filter the list and figure out the next guess
        new_solutions = []
        new_weights = []
        for word, weight in zip(possible_solutions, weights):
            if wi.is_valid_word(word):
                new_solutions.append(word)
                new_weights.append(weight)

        possible_solutions = tuple(new_solutions)
        weights = tuple(new_weights)
        if verbose:
            print(
                f"  Guess {guess_count}: {guess}. {out} {len(possible_solutions)} words remaining."
            )
            if len(possible_solutions) < 10:
                print(f"  Possible solutions: {possible_solutions}")

        key = (guess, out, len(possible_words))

        ranked_guesses = rank_guesses(possible_words, possible_solutions, weights, wi)

        if len(ranked_guesses) == 0:
            print("  Error! No more possible solutions.")
            return 7

        # In Hard mode, the guess must be in the possible solutions.
        if not hard_mode:
            guess = ranked_guesses[0][1]
        else:
            for val, word in ranked_guesses:
                if word in possible_solutions:
                    guess = word
                    break

        if out == "=====":
            if verbose:
                print("  Won!")
            return guess_count

        # Stop after 6 turns.
        if guess_count == 6:
            print("  Lost")
            return 7


runs = {
    "Wordle": {
        "initial_guess": "lares",
        "word_list": wordle_guesses,
        "weights": wordle_weights,
    },
    "12Dict": {
        "initial_guess": "tares",
        "word_list": twelve_dict_words,
        "weights": twelve_dict_weights,
    },

}
#%%
for name, details in runs.items():
    initial_guess = details["initial_guess"]
    word_list = details["word_list"]
    weights = details["weights"]

    normal_results = []
    hard_results = []
    for idx, answer in enumerate(wordle_answers, 1):
        print(f"{idx} / {len(wordle_answers)}")
        res = play_game(answer, initial_guess, word_list, weights, verbose=True)
        # print(f'{idx} {answer}: Took {res} guesses')
        normal_results.append((answer, res))

        res = play_game(
            answer, initial_guess, word_list, weights, verbose=True, hard_mode=True
        )
        hard_results.append((answer, res))

    # Easily pass from pypy back to  Python
    with open(f"{name} Simulation.pickle", "wb") as f:
        pickle.dump({"normal": normal_results, "hard": hard_results}, f)
#%%


def print_game_stats(all_results):
    """
    Prints the game statistics.

    :param all_results: A list of (word, score) tuples.
    """
    turns = [x[1] for x in all_results]
    count = Counter(turns)
    for idx in range(2, 9):
        print(
            f"{idx}: {count[idx]} /  {len(turns)} = {count[idx] / len(turns)*100:.1f}%"
        )
    print("Failed words:")
    for word, t in all_results:
        if t == 7:
            print(word)
        if t == 8:
            print(f"{word} (missing from dict)")


for name in runs:
    print(f"Stats for {name}")
    with open(f"{name} Simulation.pickle", "rb") as f:
        res = pickle.load(f)
        normal_results = res["normal"]
        hard_results = res["hard"]

    print_game_stats(normal_results)
    print_game_stats(hard_results)
