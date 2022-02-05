# Optimal Wordle Solver

An optimal Wordle strategy based on information theory.

I saw some other Wordle strategies based either on random guessing or letter
position/frequency analysis. However, no-one seemed to approach it from a
simulation/information theory perspective. This strategy identifies the guess
that on average leaves the fewest possible words remaining. It is likely near
optimal in Normal mode, but loses to some edge cases in Hard mode.

Using historical Wordles #1-#225, it has achieved a 100% win percentage in
Normal mode and a 94.2% win percentage in Hard mode.

The best starting words using the Wordle dictionary are given below. See the
full rankings in ``wordle_opening_guesses.csv``.

1. lares
2. rales
3. tares
4. soare
5. reais


## Can You Use It?

This code isn't set up to be used on live games. The purpose (and fun) of
writing it was to think about the approach, implement it and see the final
performance. Using this optimal solver for real play would take the fun away,
and there are better ways to cheat if you just want a good score.

That being said, the code is reasonably well documented and organized. If you
know Python, you can probably set it up for a live game. I recommend using
[PyPy](https://www.pypy.org/) for a performance boost because the code is slow.

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

The simulation logic is all in the :class:`WordleInformation` class. It can
determine if words match the existing information
(:meth:`WordleInformation.is_valid_word`), and create an updated object with the
latest information from another guess (meth:`WordleInformation.make_guess).

The value of any particular guess is implemented in :func:`get_guess_value`. All
the guesses are combined in :func:`rank_guesses`. However, it is very slow, so
not all guesses should be ranked at once.

## Word List Choices

The main free parameter is to choose which word list to use. If the word list is
too short, it may not contain the answer to some puzzles and the algorithm will
fail. If the list is too long, the algorithm may get bogged down eliminating
guesses that cannot be true. Long lists also require much more processing time
(See Performance Issues).

I first combined the ``2of12inf.txt`` and ``3of6all.txt`` lists from the
[12Dicts](http://wordlist.aspell.net/12dicts/), which provided 5,486 five-letter
words. Unfortunately, Wordle #88 ("golem") and #176 ("masse") are not present in
the list, which results in guaranteed losses.

The official [Wordle list](https://github.com/tabatkins/wordle-list/) contains
12,972 words and determines which guesses are permitted. However, some of the
words seem made up, ike "lotsa", "moobs", and "urbex". I suspect the Wordle
solutions draw from a smaller list because players need to be able to guess the
solutions! This aligns with the algorithm results. If words were randomly chosen
from the official list, then only around 42% of past solutions should have been
in the 12Dict list. However, 99.1% of past solutions are in the list (as of
2022/01/31).

## Normal Vs Hard Mode

Wordle has two modes: normal and hard. In Normal mode, any word can be guessed,
even if it doesn't match the information. In Hard mode, the guess must meet all
of the information. Hard mode can be enabled in the settings in the upper right
corner.

In easy mode, the list of possible guesses remains constant over the game.
Occasionally, it is advantageous to guess known invalid words because the
invalid word provides significantly more information than any valid words would
provide. 

For example, Wordle #50 was "pound". You may quickly find the last four letters
are "ound", but that matches "bound", "found", "hound", "lound", "mound",
"pound, "round", "sound" and "wound". Guessing each word individually will take
too many rounds. However, a guess like "bumph" can clear through several words
at once by including the first letter of four words in different positions.

In hard mode, guesses must match the information, so it is likely a player will
lose that situation. In this case, number of guesses shrinks over time as the
information limits the word list. In Hard mode, beating Wordle #50's "pound"
would be up to chance.

# Algorithm Performance

The algorithm was tested against Wordle answers #1-#225, available
[here](https://www.reviewgeek.com/todays-wordle-answer/). It played in Normal
mode and Hard mode for the following two word lists

* 12Dict list: 5,486 words from ``2of12inf.txt`` and ``3of6all.txt`` lists. The
  starting guess was "tares".
* Wordle List: the 12,972 allowable guesses in Wordle. The starting guess was
  "lares".


## Normal Mode

The algorithm does very well in Normal mode. The 12Dict list did not contain the
words "masse" and "golem" which resulted in two losses and a 99.1% win
percentage. The full Wordle list never lost, but took about 0.4 guesses more on
average to win. 

|  Winning Guess #  | 12Dict List Percentage | Wordle List Percentage |
| :---------------: | :--------------------: | :--------------------: |
|         2         |          0.9%          |          0.0%          |
|         3         |         33.3%          |         18.2%          |
|         4         |         57.8%          |         58.7%          |
|         5         |          6.7%          |         21.8%          |
|         6         |          0.4%          |          1.3%          |
|       Lost        |          0.0%          |          0.0%          |
| Missing from List |          0.9%          |          0.0%          |

## Hard Mode

The algorithm did slightly worse in Hard mode, with true losses. These failures
are usually from words that share many possible letters. The 12Dict list lost to
"pound", "lusty", "hatch", "jaunt", "gaudy" and "chill", in addition to the two
missing words "masse" and "golem".

Interestingly, the 12Dict list had a higher percentage of early wins in Hard
mode. I think it is because all guesses in Hard mode can be the true word.

|  Winning Guess #  | 12Dict List Percentage | Wordle List Percentage |
| :---------------: | :--------------------: | :--------------------: |
|         2         |          2.2%          |          0.4%          |
|         3         |         36.0%          |         17.3%          |
|         4         |         42.7%          |         43.6%          |
|         5         |         10.7%          |         22.7%          |
|         6         |          4.4%          |         10.2%          |
|       Lost        |          2.7%          |          5.8%          |
| Missing from List |          0.9%          |          0.0%          |

# Information Theory Connection

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

> **_NOTE:_** I represent outputs using text, where "-" is a gray box, "+" is a
> yellow box and "=" is a green box. For example, "-+---" means one yellow in
> the second position and grays elsewhere.

Another way to think about guesses is that each guess groups the remaining words
under one of the possible outputs (e.g. "-----", "----+", etc). Ideally, the
words are evenly distributed across all the 243 outputs (ignoring the fact that
some of those states are impossible like "====+"). If a guess places a lot of
words in a single output category, then there are more words to sort through. In
addition, more words makes the output category more likely. If one category has
100 words, and another only has 10 words, the first is 10x more likely to
contain the true word.

This method of thinking shows that the averaging approach in the algorithm is
approximately computing the mean squared output category size. For each possible
truth word, the number of remaining words is approximately equal to the output
category size N. After iterating over all the words, each category will be
counted N times (one for each word in the group).

This is still an approximation because a word can match multiple outputs. For
example, if the guess is "hitch", then the word "aught" matches both "--+-=" and
"--+-+". This occurs because "h" is repeated twice in the word.

## Key Assumption

One key assumption in this analysis is that all groups of N words require
approximately the same number of guesses to sort through. This is likely true
for Normal mode, where any word on the list can be guessed, but fails for Hard
mode.

For example, consider the following group of nine words: ['bound', 'found',
'hound', 'lound', 'mound', 'pound', 'round', 'sound', 'wound']. In Normal mode,
guesses like "barfs" or "balms" can eliminate multiple options at once, clearin
g through the list in a few guesses. In Hard mode, each word must be eliminated
individually, taking up to nine guesses in the worst case.

# Potential Improvements

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
guess. If the same first guess is reused, then the first guess outputs can be
cached for all the possible information outputs.

The slow step is :meth:`WordleInformation.is_valid_word`, which has been
optimized as much as I can for pure Python. The main optimizations that helped
are listed below. 

* Use Python sets for the list of possible characters rather than strings.
  Python sets have O(1) search time, while lists will have O(M)
* Switch to [PyPy](https://www.pypy.org/). This sped up my code 4x-6x just by
  changing the command!
* Use
  [``multiprocessing``](https://docs.python.org/3/library/multiprocessing.html).
  Parallelizing things never hurts.
* Made :class:`WordleInformation` objects hashable so I can use
  :func:`python.functools.lru_cache` to cache results from
  :func:`get_guess_value` and :func:`rank_guesses`.
* Use :func:`python.functools.lru_cache` to cache :func:`get_guess_value` and
  :func:`rank_guesses`. This was a 10x-20x speed boost!

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

## Duplicated letter information.

The :class:`WordleInformation` objects don't propperly apply yellow and gray
tiles when the tiles have duplicated letters. I don't know how Wordle handles
it, so I'll have to wait for those days. See the example below.

```
Your guess: papal
Solution:   apple
Output:     ++=-+
```

The current objects will only check for the "p" in the middle, but not
additionally require a second "p". I chose to discard this information because
the logic of dealing wtih this kind of event between guesses is unclear.

This issue leads to a loss in one of the Hard mode Wordles, where the same word
was guessed twice. The word "chili" was guessed twice when the true answer was
"chill".

## Weighted Guesses

Right now, I assume all words are equally likely solutions to the Wordle, but it
might be beneficial to weight common words more highly. This would allow for a
larger potential word set while still emphasizing that known words are more
likely.

12Dicts has a frequency based list: ``2+2+3freq.txt`` that could be used here.
However, I'm not sure what the weightings should be. Dealing with non-uniform
weights would also require codebase updates.

## Minimax Guess Value

Right now, the code approximately minimizes the mean squared bin size (see the
information theory section for a discussion of this). Another possible option is
to minimize the maximum bin size. This would penalize large bin sizes more.

I'm not sure how much this will improve results because mean squared bin size
already heavily penalizes larger bins, but it may be interesting later.

## Improve Hard Mode Guesses

The algorithm for hard mode needs to look further ahead than one guess to avoid
groups of very simliar words, like ['bound', 'found', 'hound', 'lound', 'mound',
'pound', 'round', 'sound', 'wound']. Once a state like this is reached, some
losses are inevitable. Ideally, the algorithm could detect when these cases
occur a couple steps in advance and make better guesses to split up these kind
of groups.

There should be some sort of recursive algorithm that can take a list of words
and figure out the maximum number of guesses to solve it. The base cases of
matches or one word remaining are simple, and the algorithm could build up from
there.

I'm not sure how computationally feasible this is; it's sort of playing every
possible game. Bad guesses can get pruned early on and caching results probably
helps. Is that enough for a reasonable runtime? I don't know.

I think this would result in truly optimal play if it can be run from the first
step.

# Licensing

This solver is licensed under GPL v3. The 12Dicts lists are [widely
distributable](http://wordlist.aspell.net/12dicts-readme/#conclude), provided
the "agid.txt" is included.
