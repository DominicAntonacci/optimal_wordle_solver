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

    * Green tiles will set the possible letter list to the single letter.
    * Yellow tiles will remove the letter from that position and add it as
    required letter.
    * Gray tiles will remove the possible letter from all lists
    """

    def __init__(self, possible_letters=None, required_letters=None):
        """
        :param possible_letters: A list of 5 sets storing the possible letters
            for each letter position.
        :param required_letters: A dictionary where the key is a letter and the
            value is the number of times that letter must appear.
        """
        # The possible letters for each position.
        if possible_letters is None:
            self.possible_letters = [
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
            ]
        else:
            self.possible_letters = possible_letters

        # A required letter must be in the word, but has an unknown position
        # (yellow tile). The key is the letter and the value is the number of
        # times that letter must appear.
        if required_letters is None:
            self.required_letters = {}
        else:
            self.required_letters = required_letters

    def _members(self):
        """
        Helper function for __hash__ and __eq__.

        https://stackoverflow.com/a/45170549
        """
        pl = tuple((frozenset(x) for x in self.possible_letters))
        rl = tuple(sorted(self.required_letters))
        return (pl, rl)

    def __hash__(self):
        return hash(self._members())

    def __eq__(self, other):
        return self._members() == other._members()

    def is_valid_word(self, word):
        """
        Returns True if the word meets the information.
        """
        # Check letters
        for idx in range(5):
            if word[idx] not in self.possible_letters[idx]:
                return False

        for letter, req_count in self.required_letters.items():
            if word.count(letter) < req_count:
                return False

        return True

    def add_green_match(self, idx, letter):
        """
        Updates the information for a green match.

        The possible letters for that index are updated and an additional
        required letter is added.
        """
        self.possible_letters[idx] = set(letter)
        if letter not in self.required_letters:
            self.required_letters[letter] = 0
        # TODO Handle multiple letter?
        self.required_letters[letter] = 1

    def add_yellow_match(self, idx, letter):
        """
        Updates the information for a yellow match.

        The letter is known not to be in that position, but is somewhere else.
        """
        try:
            self.possible_letters[idx].remove(letter)
        except KeyError:
            pass
        if letter not in self.required_letters:
            self.required_letters[letter] = 0
        # TODO Handle multiple letters?
        self.required_letters[letter] = 1

    def add_gray_match(self, idx, letter):
        """
        Updates the information for a gray tile.
        """
        for idx in range(5):
            try:
                self.possible_letters[idx].remove(letter)
            except KeyError:
                pass

    def make_guess(self, guess, true_word):
        """
        Makes a guess and returns a new information object.

        The new information object contains all the information stored in this
        object and the new information from the guess.

        :param guess: The guessed word.
        :param true_word: The true word.

        :returns: A new WordleInformation object, squarestr. The square string
            uses = as green, + as yellow and - as gray.
        """
        wi = copy.deepcopy(self)
        true_counts = Counter(true_word)

        results = list("-----")
        # Handle gren tiles first to remove those from the true counts.
        for idx, gl in enumerate(guess):
            # Green tile
            if gl == true_word[idx]:
                results[idx] = "="
                wi.add_green_match(idx, gl)
                true_counts.subtract(gl)

        # Yellow tiles
        for idx, gl in enumerate(guess):
            # Skip green tiles
            if results[idx] == "=":
                continue
            # Additional tiles are left
            if true_counts[gl] > 0:
                results[idx] = "+"
                wi.add_yellow_match(idx, gl)
                true_counts.subtract(gl)

        # Gray tiles: TODO fix this for double letters. Right now, it only works
        # if the letter is never used.
        for idx, gl in enumerate(guess):
            if gl not in true_word:
                wi.add_gray_match(idx, gl)

        return wi, "".join(results)


def test_is_valid_word():
    """
    Poor man's unit test because I'm lazy.
    """
    wi = WordleInformation()

    # # Play around with word length.  I dropped the len() check for performance.
    # assert not wi.is_valid_word("abc")
    # assert not wi.is_valid_word("abcdef")
    # assert wi.is_valid_word("abcde")

    # Play around with restricting letters
    wi.possible_letters[0] = set("abc")
    wi.possible_letters[-1] = set("xyz")
    assert not wi.is_valid_word("abcde")
    assert not wi.is_valid_word("xyzab")
    assert wi.is_valid_word("cabyz")

    # Play around requiring letter
    wi.required_letters = {
        "z": 2,
        "e": 1,
    }
    assert not wi.is_valid_word("cabyz")
    assert not wi.is_valid_word("caeyz")
    assert not wi.is_valid_word("czbyz")
    assert wi.is_valid_word("czeyz")


test_is_valid_word()


def test_make_guess():
    wi = WordleInformation()
    assert wi.make_guess("apple", "apexz")[1] == "==--+"
    assert wi.make_guess("apexz", "apple")[1] == "==+--"
    assert wi.make_guess("appep", "apple")[1] == "===+-"


test_make_guess()


def test_add_matches():
    wi = WordleInformation()
    wi.add_green_match(2, "c")
    assert wi.possible_letters[2] == set("c")
    assert wi.required_letters["c"] == 1

    wi = WordleInformation()
    wi.add_yellow_match(2, "c")
    assert "c" not in wi.possible_letters[2]
    assert wi.required_letters["c"] == 1

    wi = WordleInformation()
    wi.add_gray_match(2, "c")
    assert "c" not in wi.possible_letters[0]
    assert "c" not in wi.possible_letters[1]
    assert "c" not in wi.possible_letters[2]
    assert "c" not in wi.possible_letters[3]
    assert "c" not in wi.possible_letters[4]


test_add_matches()


@lru_cache(maxsize=1024)
def _get_remaining_words(wi, possible_words):
    """
    Returns the number of remaining words.

    This is separated so that it is cachable.

    :param wi: The WordleInformation object.
    :param possible_words: The words to filter.

    :returns: The number of words that match the object.
    """
    return sum(wi.is_valid_word(w) for w in possible_words)


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
    for word in possible_words:
        new_wi, out = wi.make_guess(guess, word)
        # The word was guessed, so there's no remaining words.
        if out == "=====":
            remaining_word_counts.append(0)
        else:
            remaining_word_counts.append(_get_remaining_words(new_wi, possible_words))

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


def process_first_guess(file_name, word_list, weights=None, block_size=64, num_threads=4):
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
        guess_values = rank_guesses(next_guesses, word_list, weights, threads=num_threads)
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
    "wordle_opening_guesses", wordle_guesses, wordle_weights, block_size=32, num_threads=4
)
    process_first_guess(
        "12Dict_guesses", twelve_dict_words, twelve_dict_weights, block_size=64
    )
    process_first_guess(
        "wordle_opening_guesses", wordle_guesses, wordle_weights, block_size=32
    )
