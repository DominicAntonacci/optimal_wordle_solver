"""
This module stores all the word lists and estimates weights for each word based
on the frequency.

* ``twelve_dict_words``: Guesses constructed from various 12Dict lists.
* ``wordle_guesses``: All possible Wordle guesses
* ``wordle_answers``: Previous Wordle answers.

* ``twelve_dict_weights``: The weights for ``twelve_dict_words``.
* ``wordle_weights``: The weights for ``wordle_guesses``.
"""
import re
# Wordle Guess list
wordle_guesses = set()
with open("wordle-list/words") as f:
    for line in f:
        wordle_guesses.add(line.strip())
wordle_guesses = tuple(wordle_guesses)

# Wordle Answer list
wordle_answers = []
with open("wordle_answers.txt") as f:
    for row in f:
        wordle_answers.append(row.split()[-1])
wordle_answers = tuple(wordle_answers)


# 12Dict list
_special_characters = ":&#=<^~+!%*!()[]"
def _parse_12dicts_list(path):
    """
    Parses the words from a 12Dicts list.
    """
    all_words = set()
    with open(path) as f:
        for line in f:
            
            line = line.strip().lower()
            # Strip out special characters.
            for char in _special_characters:
                line = line.replace(char, "")
            words = line.split(',')
            for word in words:
                word = word.strip()
                if re.match("^[a-z]{5}$", word):
                    all_words.add(word)
    return tuple(all_words)
twelve_dict_words = set()
dictionaries = [
    "./12dicts-6.0.2/American/2of12inf.txt",
    "./12dicts-6.0.2/International/3of6all.txt",
    "./12dicts-6.0.2/Special/neol2016.txt",
]
for dictionary in dictionaries:
    for word in _parse_12dicts_list(dictionary):
        twelve_dict_words.add(word)
twelve_dict_words = tuple(twelve_dict_words)

# Frequency analysis
# Parse 2+2+3frq.txt
lemma_to_freq = {}
word_to_lemma = {}
current_frequency = -1
current_lemma = ""
with open("./12dicts-6.0.2/Lemmatized/2+2+3frq.txt") as f:
    for row in f:
        row = row.lower()
        # Strip out special characters.
        for char in _special_characters:
            row = row.replace(char, "")
        # Frequency indicator.
        if row[0] == "-":
            _, num, _ = row.split(" ")
            current_frequency = int(num)
        # Words in a lemma
        if row[0] == " ":
            words = row.strip().split(", ")
            for word in words:
                word_to_lemma[word] = current_lemma
        # A new lemma
        else:
            current_lemma = row.strip()
            word_to_lemma[current_lemma] = current_lemma
            lemma_to_freq[current_lemma] = current_frequency

# Add the rest of the lemmas from 2+2+3lem.txt
with open("./12dicts-6.0.2/Lemmatized/2+2+3lem.txt") as f:
    for row in f:
        # Words in a lemma
        row = row.lower()
        # Strip out special characters.
        for char in _special_characters:
            row = row.replace(char, "")
        if row[0] == " ":
            words = row.strip().split(", ")
            for word in words:
                word_to_lemma[word] = current_lemma
        # A new lemma
        else:
            current_lemma = row.strip()
            word_to_lemma[current_lemma] = current_lemma


def word_to_freq(word):
    """
    Determines the frequency of the word.

    Frequency is defined in 12Dicts. It begins at level 1, with each level below
    containing words about half as often as the level above. I add level 22,
    which is for words not found in the frequency list.

    :param word: The word to find.

    :returns: The frequency. If it isn't present in 12Dicts, then 22 is returned
        (lower than the lowest group).
    """
    if word not in word_to_lemma:
        return 22
    lemma = word_to_lemma[word]
    return lemma_to_freq.get(lemma, 22)


def words_to_weights(guesses, answers=wordle_answers):
    """
    Determines the appropriate weight for each word frequency.

    The weight at a given frequency is the number of possible answers at that
    frequency divided by the number of guesses at that frequency. If the result
    is zero, it gets the average weight of all words with a frequency.

    :param guesses: The list of guesses.
    :param answers: The list of answers. This should be the answers given so
        far.

    :returns: A tuple of weights. The index of each weight aligns with the index
        of each guess.
    """
    # The default weight is the result for all non-22 frequencies.
    answers_at_freq = [w for w in answers if word_to_freq(w) != 22]
    guesses_at_freq = [w for w in guesses if word_to_freq(w) != 22]
    default_weight = sum(w in guesses_at_freq for w in answers_at_freq) / len(guesses_at_freq)

    # Determine the appropriate weight per word frequency.
    freq_to_weight = {}
    for freq in range(1, 23):
        answers_at_freq = [w for w in answers if word_to_freq(w) == freq]
        guesses_at_freq = [w for w in guesses if word_to_freq(w) == freq]
        try:
            weight = sum(w in guesses_at_freq for w in answers_at_freq) / len(guesses_at_freq)
        except ZeroDivisionError:
            weight = 0
        if weight != 0:
            freq_to_weight[freq] = weight
        else:
            freq_to_weight[freq] = default_weight

    # Assign the weights to words.
    return tuple([freq_to_weight[word_to_freq(word)] for word in guesses])

twelve_dict_weights = words_to_weights(twelve_dict_words)
wordle_weights = words_to_weights(wordle_guesses)