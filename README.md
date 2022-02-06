# Optimal Wordle Solver

An optimal Wordle strategy based on information theory.

I saw some other Wordle strategies based either on random guessing or letter
position/frequency analysis. However, no-one seemed to approach it from a
simulation/information theory perspective. This strategy identifies the guess
that on average leaves the fewest possible words remaining. It is likely near
optimal in Normal mode, but loses to some edge cases in Hard mode.

Using historical Wordles #1-#230, it has achieved a 100% win percentage in
Normal mode and a 98.7% win percentage in Hard mode.

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

The Wordle output is computed using :func:`make_guess`, which can be stored in a
:class:`WordleInformation` object. These objects store the current game state
and can determine which words match the current information with
:meth:`is_valid_word`. The value of any particular guess is implemented in
:func:`get_guess_value`. All the guesses are combined in :func:`rank_guesses`.

## Word List Choices

The main free parameter is to choose which word list to use. If the word list is
too short, it may not contain the answer to some puzzles and the algorithm will
fail. If the list is too long, the algorithm may get bogged down eliminating
guesses that cannot be true.

I first combined the ``2of12inf.txt`` and ``3of6all.txt`` lists from the
[12Dicts](http://wordlist.aspell.net/12dicts/), which provided 5,486 five-letter
words. Unfortunately, Wordle #88 ("golem") and #176 ("masse") are not present in
the list, which results in guaranteed losses.

The official [Wordle list](https://github.com/tabatkins/wordle-list/) contains
12,972 words and determines which guesses are permitted. However, some of the
words seem made up, ike "lotsa", "moobs", and "urbex". I suspect the Wordle
solutions draw from a smaller list because players need to be able to guess the
solutions! 

A cursory analysis of Wordle answers #1-225 confirms this suspicion; 99.1% of
past solutions are present in the 12Dicts list. If the answers were drawn
randomly from the Wordle list, only 42% of past solutions should be on the
12Dicts list.

### Answer Weighting + Frequency Analysis

12Dicts also provides the ``2+2+3frq.txt`` list, which organizes lemmas (word
bases) based on frequency of use. There are 21 levels, with level 1 containing
the most common words and each subsequent level containing words used
approximately half as frequently. I defined a 22nd level for words not found in
this frequency list. Then, ``2+2+3lem.txt`` can be used to map all the lemmas to
words.

With these lists, possible words and historical answers can be grouped by their
frequency level. Intuitively, frequency levels with lots of historical answers
should be prioritized over other levels.

This is achieved by assigning each frequency level a weight calculated as the (#
of answers at the frequency level) / (# of possible words the frequency level).
If level 15 has a higher weighting than level 17, it implies that words at level
15 are more likely to be correct. Any levels without a historical Wordle answer
are assigned the average weight of levels 1-21.

The averaging step in :func:`get_guess_value` was updated to use a weighted
average according to these weights. This indirectly influences which word to
guess by playing with the weighting function present. It still allows any word
to be guessed (in Normal mode), but will prefer common words near the end.

In practice, levels 1-21 have fairly similar weights, with lower a slight
preference for lower levels. 63% of the possible Wordle guesses are not present
in the frequency list and assigned level 22. With only 1.4% of historical
guesses at that level, it's heavily penalized.

Weighting answers only had minor changes to the first-guess lists. The top
guesses remained the same and the overall ranking was similar, with occasional
words swapping places. The main benefit comes in later guesses when the word
list is significantly smaller. In this case, common words are more likely to be
guessed because they are weighted more heavily.

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

The algorithm was tested against Wordle answers #1-#230, available
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
|         2         |          1.7%          |          0.9%          |
|         3         |         38.7%          |         36.5%          |
|         4         |         54.8%          |         56.1%          |
|         5         |          3.5%          |          6.5%          |
|         6         |          0.4%          |          0.0%          |
|       Lost        |          0.0%          |          0.0%          |
| Missing from List |          0.9%          |          0.0%          |

## Hard Mode

The algorithm did slightly worse in Hard mode, with true losses. These failures
are usually from words that share many possible letters. The 12Dict list lost to
"pound", "lusty", "hatch", "jaunt", "gaudy" and "chill", in addition to the two
missing words "masse" and "golem".

Interestingly, both lists have a higher percentage of early wins in Hard mode. I
think it is because all guesses in Hard mode can be the true word.

|  Winning Guess #  | 12Dict List Percentage | Wordle List Percentage |
| :---------------: | :--------------------: | :--------------------: |
|         2         |          2.6%          |          2.2%          |
|         3         |         39.6%          |         34.3%          |
|         4         |         46.5%          |         48.7%          |
|         5         |          8.3%          |         12.2%          |
|         6         |          0.9%          |          1.3%          |
|       Lost        |          1.3%          |          1.3%          |
| Missing from List |          0.9%          |          0.0%          |

# Information Theory Connection

Feel free to skip this section! It may not make sense if you haven't taken an
information theory class.

The theory behind this approach is to choose guesses that minimize the overall
entropy of the system. The true word is modeled as a discrete random variable
with each value representing one of the possible words. I assume all words are
equally probable, which simplifies the math some and allows me to get away with
counting distinct elements rather than deal with probabilities.

The information provided by a guess is discrete: once the information is added,
the probability of some values will drop to 0 and the other probabilities will
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
guesses like "barfs" or "balms" can eliminate multiple options at once, clearing
through the list in a few guesses. In Hard mode, each word must be eliminated
individually, taking up to nine guesses in the worst case.

# Optimizations

This section highlights some of the changes I made to get significant
performance gains. They might be able to help you too!

Naive implementations of this algorithm are O(N^3), with N being the number of
words to check. Each simulation takes O(N) to filter the list of words. N
simulations are created (one for each truth word) for each guess. N guesses are
made in total. 

The first easy step was switching to [PyPy](https://www.pypy.org/) and setting
up the code for
[``multiprocessing``](https://docs.python.org/3/library/multiprocessing.html).

The next step was to cache useful results. This required making
:class:`WordleInformation` hashable, but saved redoing a lot of computations.
The first big savings was in :func:`get_guess_value`. For a given guess, there's
only a maximum of 243 possible outputs, even though I may be checking thousands
of words. By caching the remaining words of each output, I effectively eliminate
one of the for loops, dropping the algorithm to O(N^2).

The second big savings was to cache :func:`rank_guesses`, which pays off when
running :func:`play_game`. In a similar manner, there are only a maximum of 243
possible second guesses (and in practice, many fewer), so caching this saves
repeating those calculations.

Then, there were a few other hacks to speed things up. Read the code if you want
to see them; they aren't good coding practices, but they sure were fast!

# Potential Improvements

## Minimax Guess Value

Right now, the code approximately minimizes the mean squared bin size (see the
information theory section for a discussion of this). Another possible option is
to minimize the maximum bin size. This would penalize large bin sizes more.

I'm not sure how much this will improve results because mean squared bin size
already heavily penalizes larger bins, but it may be interesting later. It might
already be moot now that weighted averaging is used. I also think the improved
hard mode guesses will work better.

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
