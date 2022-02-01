# Optimal Wordle Solver

An optimal Wordle strategy based on information theory.

I saw some other Wordle strategies based either on random guessing or letter
position/frequency analysis. However, no-one seemed to approach it from a
simulation/information theory perspective. Provided the starting list of words
is correct, this play should be theoretically optimal (if cheating is excluded).

It's currently achieved a 99.1% win percentage on historical Wordles (until
2022/01/30), only failing two not in the starting list. In Hard Mode, it has achieved a 96.4% win percentage, only losing to 8 words (including the two not on the list).

The best starting words using the five-letter words from the 12Dicts word list
are given below. See the full rankings in ``opening_guesses.csv``.

1. aries (not valid Wordle word)
2. tares
3. rates
4. aloes
5. tales

# Approach

The overall approach is to simulate all possible outcomes of all possible
guesses and then choose the guess with the best outcome. The flow is as follows

1. Choose a guess from the list of five-letter words.
2. Start a simulation for each word in the possible words where I assume that
   word is truth 
   1. Determine the Wordle output if I make the guess for the assumed truth
      word.
   2. Count the number of words that match this output (and previous outputs if
      this is a later guess).
3. The guess's final score is the average result across all simulations. Lower
   scores are better because it means there are fewer words to sort through in
   later rounds.
4. Repeat steps 1-3 for all possible guesses.
5. The best guess is the one with the lowest score.

The word list is generated using the
[12Dicts](http://wordlist.aspell.net/12dicts/) package , which has word lists
for various purposes. Based off the suggestions on the site, I decided to use
all five-letter words from the ``2of12inf.txt`` and ``3of6all.txt`` lists. I
later discovered that the [wordle
list](https://github.com/tabatkins/wordle-list/) is available and will use that
for a later run.

The simulation logic is all in the :class:`WordleInformation` class. It can
determine if words match the existing information
(:meth:`WordleInformation.is_valid_word`), and create an updated object with the
latest information from another guess (meth:`WordleInformation.make_guess).

The value of any particular guess is implemented in :func:`get_guess_value`. All
the guesses are combined in :func:`rank_guesses`. However, it is very slow, so
not all guesses should be ranked at once.

## Normal Vs Hard Mode

Wordle has two modes: normal and hard. In Normal mode, any word can be guessed, even if it doesn't match the information. In Hard mode, the guess must meet all of the information. Hard mode can be enabled in the settings in the upper right corner.

In easy mode, the list of possible guesses remains constant over the game.
Occasionally, it is advantageous to guess known invalid words because the invalid word provides significantly more information than any valid words would provide. 

For example, Wordle #50 was "pound". You may quickly find the last four letters
are "ound", but that matches "bound", "found", "hound", "mound", "pound, "sound"
and "wound". Guessing each word individually will take too many rounds. However,
a guess like "bumph" can clear through several words at once by including the
first letter of four words in different positions.

In hard mode, guesses must match the information, so it is likely a player will lose that situation. In this case, number of guesses shrinks over time as the information limits the word list. In Hard mode, beating Wordle #50's "pound" would be up to chance.

## Information Theory Connection

Feel free to skip this section! It may not make sense if you haven't taken an
information theory class.

The theory behind this approach is to choose guesses that minimize the overall
entropy of the system. The true word is modeled as a discrete random variable
with each value representing one of the possible words. I assume all words are
equally probable, which simplifies the math some and allows me to get away with
counting distinct elements rather than deal with probabiltiies.

The information provided by a guess is discrete: once the information is added,
the probability of some values will drop to 0 and the other probabilties will
scale accordingly. This means the way to minimize entropy is to remove the most
possible words with a single guess. This also means we are picking the guess
that will provide the most information about the unknown word.

# Algorithm Performance

The algorithm was provided the 5,486 five-letter words from 12Dicts's ``2of12inf.txt`` and ``3of6all.txt`` lists and always used the starting guess "tares". It was run in both normal mode, where all 5,486 possible guesses are considered for every round, and in hard mode, where only possible solutions are considered in each round.

The algorithm was tested against Wordle answers #1-#225, avaiable [here](https://www.reviewgeek.com/todays-wordle-answer/). 

## Normal Mode

In Normal mode, the algorithm achieved a 99.1% win percentage, usually winning in
4 turns. The only losses were for two answers that were not missing from the
12Dicts list ("masse" and "golem")

|  Winning Guess #  | Percentage |
| :---------------: | :--------: |
|         2         |    0.9%    |
|         3         |   33.3%    |
|         4         |   57.8%    |
|         5         |    6.7%    |
|         6         |    0.4%    |
|       Lost        |    0.0%    |
| Missing from List |    0.9%    |

## Hard Mode

In Hard mode, the algorithm achieved a 96.4% win percentage, usually winning in 3-4 turns.

|  Winning Guess #  | Percentage |
| :---------------: | :--------: |
|         2         |    2.2%    |
|         3         |   36.0%    |
|         4         |   42.7%    |
|         5         |   10.7%    |
|         6         |    4.4%    |
|       Lost        |    2.7%    |
| Missing from List |    0.9%    |

The failures occurred because several guesses shared many letters. The six words the algorithm lost to were "pound", "lusty", "hatch", "jaunt", "gaudy" and "chill".

# Word List Choices

The main free parameter in this algorithm is which word list to use. If the word list is too short, it may not contain the answer to some puzzles and the algorithm will fail. If the list is too long, the algorithm may get bogged down eliminating guesses that cannot be true. Long lists also require much more processing time (See Performance Issues).

The 12Dict lists are a great starting place because the the lists are curated to
avoid misspellings and other small issues. I combine the ``2of12inf.txt`` and
``3of6all.txt`` ists to get 5,486 five-letter words. The algorithm results are
very satisfying, but it is missing two words from past Wordle solutions. In
addition, the best guess with these sets is "aires", but that isn't a valid
Wordle word, so "tares" is the next best result. This list took around 6 hours to process on my computer.

The official Wordle list contains 12,972 words and determines which guesses are permitted. However, some of the words seem made up, ike "lotsa", "moobs", and "urbex". I suspect the Wordle solutions draw from a smaller list because players need to be able to guess the solutions! This aligns with the algorithm results. If words were randomly chosen from the official list, then only around 42% of past solutions should have been in the 12Dict list. However, 99.1% of past solutions are in the list (as of 2022/01/31). 

# Potential Improvements

## Duplicated letter information.

The :class:`WordleInformation` objects don't propperly apply yellow and gray tiles when the tiles have duplicated letters. I don't know how Wordle handles it, so I'll have to wait for those days. See the example below.

```
Your guess: papal
Solution:   apple
Output:     ++=-+
```

The current objects will only check for the "p" in the middle, but not additionally require a second "p". I chose to discard this information because the logic of dealing wtih this kind of event between guesses is unclear.

## Performance Issues

Determining the optimal first guess is very slow. Luckily, it only needs to be
done once! It currently takes my computer about 3.5 seconds per guess, which is
about 5 hours to iterate through all the possible guesses.

The main problem is that the algorithm is O(N^3), with N being the number of
words to check. Each simulation takes O(N) to filter the list of words. N
simulations are created (one for each truth word) for each guess. N guesses are
made.

This means subsequent guesses should be much faster (on the order of seconds)
because the list of possible words will shrink so significantly after the first
guess. If the same first guess is reused, then the first guess outputs can be cached for all the possible information outputs.

The slow step is :meth:`WordleInformation.is_valid_word`, which has been
optimized as much as I can for pure Python. The main optimizations that helped
are listed below

* Use Python sets for the list of possible characters rather than strings.
  Python sets have O(1) search time, while lists will have O(M)
* Switch to [PyPy](https://www.pypy.org/). This sped up my code 4x-6x just by
  changing the command!
* Use
  [``multiprocessing``](https://docs.python.org/3/library/multiprocessing.html).
  Parallelizing things never hurts.

I considered a few other optimization ideas, but they were either too
complicated or not faster. I may revisit these ideas in the future if
performance is too big of a concern.

* Regular expressions: I found a custom ``is_valid_word`` was faster than
  implementing regex searches. I think it's because my custom expression can
  short-circuit once a word is known to not match the rules.
* Invert my search terms: Rather than maintain a list of possible letters,
  maintain a list of invalid letters. It was slower, but I'm not sure why.
* [Numba](https://numba.pydata.org/): It was slower than regular Python. Their
  documentation says it can be [slow for string
  operations].(https://numba.pydata.org/numba-doc/dev/reference/pysupported.html#str)
* [Cython](https://cython.org/): This was confusing and I wasn't sure how to get
  sets to work.
* NumPy Vectorization: This is promising, but I haven't spent enough time to
  figure out how to do it. Because all the words are 5 letters, the words can be
  stored as a NumPy array. If I can vectorize ``is_valid_word``, there could be
  some major performance gains. I think this may be easiest if combined with
  inverting the search terms. NumPy also doesn't work with PyPy, so it would
  have to be one or the other.
* Write in a fast language: This is likely the best option, but it's been a
  while since I've used C++. Maybe it's a chance to learn Go.