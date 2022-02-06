"""
An optimal Wordle strategy based on information theory.
"""
#%%
import copy
import csv
import pickle
import re
import time
from collections import Counter
from functools import partial, lru_cache
from multiprocessing import Pool
from pathlib import Path

from word_lists import (
    twelve_dict_words,
    twelve_dict_weights,
    wordle_guesses,
    wordle_weights,
)


#%%
class WordleInformation:
    """
    A class to store the information given from previous guesses.

    The information is stored in three parts:

    * ``possible_letters``: The possible letters for each index. A tuple of
      frozensets.
    * ``minimum_letters``: The minimum number of letters required in a word.
      These are determined from green and yellow tiles.
    * ``maximum_letters``: The maximum number of letters required in a word.
      These are determined from the gray tiles.
    """

    def __init__(self, previous_wi=None, guess=None, output=None):
        """
        :param previous_wi: The previous :class:`WordleInformation` object. The
            guess and output will be added to this information. If None, start
            fresh.
        :param guess: The most recent guess. If None, no guess is added.
        :param output: The most recent output as a string of "-+=". If None, no
            output is added.
        """
        # Create the fields
        if previous_wi is None:
            possible_letters = [
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
            ]
            minimum_letters = {}
            maximum_letters = {}
        else:
            possible_letters = [set(x) for x in previous_wi.possible_letters]
            minimum_letters = previous_wi.minimum_letters.copy()
            maximum_letters = previous_wi.maximum_letters.copy()

        # Incorporate the new guess if necessary.
        if guess is not None and output is not None:
            new_min = {}
            new_max = {}

            # Process green and yellow first.
            for idx, (letter, symbol) in enumerate(zip(guess, output)):
                # Green
                if symbol == "=":
                    possible_letters[idx] = set(letter)
                    if letter not in new_min:
                        new_min[letter] = 0
                    new_min[letter] += 1

                if symbol == "+":
                    try:
                        possible_letters[idx].remove(letter)
                    except KeyError:
                        pass
                    if letter not in new_min:
                        new_min[letter] = 0
                    new_min[letter] += 1

            # Process gray last because it required new_min to be populated. A
            # gray symbol comes out when no more letters are in the output.
            for idx, (letter, symbol) in enumerate(zip(guess, output)):
                if symbol == "-":
                    if letter not in new_max:
                        new_max[letter] = 0
                    new_max[letter] = new_min.get(letter, 0)

                    # If the letter isn't in the word, remove it from the
                    # required lists. These check faster than this max check.
                    if new_max[letter] == 0:
                        for idx in range(5):
                            try:
                                possible_letters[idx].remove(letter)
                            except KeyError:
                                pass

            for letter, val in new_min.items():
                minimum_letters[letter] = max(val, minimum_letters.get(letter, 0))
            maximum_letters.update(new_max)

        # The minimum number of letters must be at least as big as the number of
        # greens, even from previous guesses.
        for idx in range(5):
            if len(possible_letters[idx]) > 1:
                continue
            to_match = possible_letters[idx]
            letter = list(to_match)[0]
            num_matches = sum(x == to_match for x in possible_letters)
            minimum_letters[letter] = max(num_matches, minimum_letters[letter])

        # Finalize the object
        self.possible_letters = tuple(frozenset(x) for x in possible_letters)
        self.minimum_letters = minimum_letters
        self.maximum_letters = maximum_letters

    def is_valid_word(self, word):
        """
        Returns True if the word matches this object.
        """
        # Check letters
        for idx in range(5):
            if word[idx] not in self.possible_letters[idx]:
                return False

        # Check maximums
        for letter, max_count in self.maximum_letters.items():
            if word.count(letter) > max_count:
                return False

        # Check minimums
        for letter, min_count in self.minimum_letters.items():
            if word.count(letter) < min_count:
                return False

        return True

    def _members(self):
        """
        Helper function for __hash__ and __eq__.

        https://stackoverflow.com/a/45170549
        """
        pl = tuple((frozenset(x) for x in self.possible_letters))
        minl = tuple(sorted(self.minimum_letters))
        maxl = tuple(sorted(self.maximum_letters))
        return (pl, minl, maxl)

    def __hash__(self):
        return hash(self._members())

    def __eq__(self, other):
        return self._members() == other._members()


def make_guess(guess, answer):
    """
    Makes a guess and returns the output string.

    * "=" means green tile
    * "+" means yellow tile
    * "-" means gray tile.

    :param guess: The guessed word.
    :param answer: The answer.

    :returns: The five-character results string.
    """
    true_counts = Counter(answer)
    results = list("-----")
    # Handle green tiles first to remove those from the true counts.
    for idx, gl in enumerate(guess):
        if gl == answer[idx]:
            results[idx] = "="
            true_counts.subtract(gl)

    # Yellow tiles
    for idx, gl in enumerate(guess):
        # Skip green tiles.
        if results[idx] == "=":
            continue
        # Additional tiles are left
        if true_counts[gl] > 0:
            results[idx] = "+"
            true_counts.subtract(gl)

    # Gray tiles implicitly handled at creation.

    return "".join(results)


@lru_cache(maxsize=1024)
def _get_remaining_words(wi, guess, out, possible_words_str):
    """
    Returns the number of remaining words.

    This is separated so that it is cachable.

    ``possible_words_str`` is a single string with no spaces because Python
    caches string hashes, but not tuple hashes
    (https://bugs.python.org/issue1462796).

    .. note::

        :func:`~python.functools.lru_cache` hashes the inputs to store the
        results in the cache. Because most of these function calls are hashed,
        it is actually faster to pass in a string and split it into five-letter
        words here than to pass in a tuple directly. It only works because all
        the words are five letters long. It's a 2.5x speed increase, but that
        doesn't mean it's not a horrible hack.

    :param wi: The starting WordleInformation object.
    :param guess: The guess.
    :param out: The output.
    :param possible_words: The words to filter as a single string with no
        spaces.

    :returns: The number of words that match the object.
    """
    # https://stackoverflow.com/a/9475354
    # This is about twice as fast as doing it by regex.
    possible_words = (
        possible_words_str[i : i + 5] for i in range(0, len(possible_words_str), 5)
    )
    new_wi = WordleInformation(wi, guess, out)
    return sum(new_wi.is_valid_word(w) for w in possible_words)


def get_guess_value(guess, possible_words, weights=None, wi=None):
    """
    Returns the average number of remaining words for a given guess.

    Lower values are better.

    :param guess: The guess
    :param possible_words: The possible true words remaining.
    :param weights: The weight of each possible word. If None, all possible
        words are evenly weighted.
    :param wi: A WordleInformation object
    """
    if wi is None:
        wi = WordleInformation()

    if weights is None:
        weights = [1] * len(possible_words)
    remaining_word_counts = []
    possible_words = tuple(possible_words)  # Make immutable for caching.

    # Horrible hack for performance boost. See :func:`_get_remaining_words` for
    # more details.
    possible_words_str = "".join(possible_words)
    for word in possible_words:
        out = make_guess(guess, word)
        if out == "=====":
            remaining_word_counts.append(0)
        else:
            remaining_word_counts.append(
                _get_remaining_words(wi, guess, out, possible_words_str)
            )

    # Compute the weighted average.
    weighted_average = 0
    for count, weight in zip(remaining_word_counts, weights):
        weighted_average += count * weight
    weighted_average /= sum(weights)
    return weighted_average


#%%

# Hacky thing with pool so it doesn't get recreated every time this is called.
pool = Pool(4)


@lru_cache(maxsize=2048)
def rank_guesses(possible_guesses, possible_answers, weights=None, wi=None, threads=4):
    """
    Ranks guesses based on their value.

    :param possible_guesses: The possible guesses.
    :param possible_answers: The possible answers
    :param weights: The weight of each possible answer.
    :param wi: A WordleInformation object.
    :param threads: The number of CPU threads to use. If set to 1, this runs
        single-threaded for debugging purposes.
    """
    # Hack to restart the pool only if we need fewer threads.
    global pool
    if pool._processes != threads:
        pool.terminate()
        pool = Pool(threads)

    # Run explicitly single-threaded for debugging purposes.
    if threads == 1:
        values = []
        for guess in possible_guesses:
            values.append(get_guess_value(guess, possible_answers, weights, wi))

    else:
        func = partial(
            get_guess_value, possible_words=possible_answers, weights=weights, wi=wi
        )
        values = pool.map(func, possible_guesses, chunksize=len(possible_guesses) // 12)

    guess_value = list(zip(values, possible_guesses))
    return sorted(guess_value)


def process_first_guess(
    file_name, word_list, weights=None, block_size=64, num_threads=4
):
    """
    Processes the first guess.

    The first guess is computationally intensive and can take hours to process.
    This function processes groups of guesses so that it can be stopped and
    restarted easily.

    :param word_list: The list of words to use.
    :param weights: The weights to use for each word.
    :param file_name: The ending file name.
    :param block_size: The number of guesses to process at a time.
    :param num_threads: The number of threads to use.
    """
    word_list = tuple(word_list)
    # Create the pickle file if it doesn't exist.
    pickle_path = Path(file_name).with_suffix(".pickle")
    if not pickle_path.exists():
        with pickle_path.open("wb") as f:
            pickle.dump([], f)

    while True:
        with pickle_path.open("rb") as f:
            current_guess_values = pickle.load(f)

        # Determine the next guesses.
        current_guesses = [x[1] for x in current_guess_values]
        remaining_guesses = [x for x in word_list if x not in current_guesses]
        if len(remaining_guesses) == 0:
            break
        next_guesses = tuple(remaining_guesses[:block_size])
        print(f"Checking {next_guesses}")

        # Process the next guesses.
        t = time.time()
        guess_values = rank_guesses(
            next_guesses, word_list, weights, threads=num_threads
        )
        for guess in guess_values:
            print(guess)
        print(f"This block took {time.time() - t} seconds")

        # Add to the current list and dump back to a pickle
        current_guess_values.extend(guess_values)
        with pickle_path.open("wb") as f:
            pickle.dump(current_guess_values, f)

    # Dump the whole list to a CSV
    with pickle_path.open("rb") as f:
        all_guesses = pickle.load(f)

    csv_path = Path(file_name).with_suffix(".csv")
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Score", "Word"])
        writer.writerows(sorted(all_guesses))


if __name__ == "__main__":
    process_first_guess(
        "12Dict_guesses", twelve_dict_words, twelve_dict_weights, block_size=64
    )
    process_first_guess(
        "wordle_opening_guesses", wordle_guesses, wordle_weights, block_size=32
    )
