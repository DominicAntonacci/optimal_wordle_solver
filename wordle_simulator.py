"""
This scripts tests the performance for various configurations.
"""
#%%
import pickle
from collections import Counter
from wordle import WordleInformation, rank_guesses, possible_words

all_answers = []
with open("wordle_answers.txt") as f:
    for row in f:
        all_answers.append(row[-6:-1])

#%%
 
# The first guess results can be cached for improved performance. The key is
# (guess, output, len(possible_words)) and the value is the ranked results. The
# guess and len(possible_words) help ensure the cache isn't used for invalid
# guesses or word lists.
first_guess_cache = {}
with open('first_guess_cache.pickle', 'rb') as f:
    first_guess_cache = pickle.load(f)

def play_game(answer, initial_guess, possible_words, verbose=False, hard_mode=False):
    """
    Plays a game of Wordle.

    :param answer: The answer
    :param initial_guess: The initial guess to make.
    :param possible_words: The possible words list.
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
    possible_solutions = possible_words.copy()
    possible_words = possible_words.copy()  # Lose the reference.
    guess = initial_guess
    won_game = False
    guess_count = 0

    while True:
        # Make the guess and update the information
        wi, out = wi.make_guess(guess, answer)
        guess_count += 1

        # Filter the list and figure out the next guess
        possible_solutions = [x for x in possible_solutions if wi.is_valid_word(x)]
        if verbose:
            print(f"  Guess {guess_count}: {guess}. {out} {len(possible_solutions)} words remaining.")
            if len(possible_solutions) < 10:
                print(f"  Possible solutions: {possible_solutions}")

        key = (guess, out, len(possible_words))

        if guess_count == 1 and key in first_guess_cache:
            ranked_guesses = first_guess_cache[key]
        else:
            ranked_guesses = rank_guesses(possible_words, possible_solutions, wi)
            if guess_count == 1:
                first_guess_cache[key] = ranked_guesses
                with open('first_guess_cache.pickle', 'wb') as f:
                    pickle.dump(first_guess_cache, f)
   
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
            print('  Lost')
            return 7

#%%
def print_game_stats(all_results):
    """
    Prints the game statistics
    """
    turns = [x[1] for x in all_results]
    count = Counter(turns)
    for idx in range(2, 9):
        print(f"{idx}: {count[idx]} /  {len(turns)} = {count[idx] / len(turns)*100:.1f}%")
    print('Failed words:')
    for word, t in all_results:
        if t == 7:
            print(word)
        if t == 8:
            print(f'{word} (missing from dict)')



initial_guess = "tares"
all_results = []
#%%
normal_results = []
hard_results = []
for idx, answer in enumerate(all_answers, 1):
    print(f'{idx} / {len(all_answers)}')
    res = play_game(answer, "tares", possible_words, verbose=True)
    # print(f'{idx} {answer}: Took {res} guesses')
    normal_results.append((answer, res))
    
    res = play_game(answer, "tares", possible_words, verbose=True, hard_mode=True)
    hard_results.append((answer, res))

# Easily pass from pypy back to  Python
with open("simulation.pickle", "wb") as f:
    pickle.dump({'normal': normal_results, 'hard': hard_results}, f)
#%%
with open("simulation.pickle", 'rb') as f:
    res = pickle.load(f)
    normal_results = res['normal']
    hard_results = res['hard']

print_game_stats(normal_results)
print_game_stats(hard_results)
