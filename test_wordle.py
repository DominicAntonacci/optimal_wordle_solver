"""
Unit tests for Wordle.

I prefer pytest, but am using unittest to avoid the dependency and ensure this works with PyPy.
"""
import unittest

from wordle import WordleInformation, get_guess_value, make_guess


class TestWordle(unittest.TestCase):
    def test_is_valid_word(self):
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



    def test_make_guess(self):
        wi = WordleInformation()
        assert make_guess("apple", "apexz") == "==--+"
        assert make_guess("apexz", "apple") == "==+--"
        assert make_guess("appep", "apple") == "===+-"

    def test_add_matches(self):
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


    def test_get_guess_value(self):
        """
        Tests get_guess_value.

        Guess/answer mappings.

        * grain/grain: ===== Score 0
        * grain/grown: ==--= Score 1 (only grown remaining)
        * grain/stews: ----- Score 2 (stews/weeds remaining)
        * grain/weeds: ----- Score 2 (stews/weeds remaining)
        """
        guess = 'grain'
        possible_words = ['grain', 'grown', 'stews', 'weeds']

        avg = get_guess_value(guess, possible_words)
        self.assertAlmostEqual(avg, 5/4)

        weighted_avg = get_guess_value(guess, possible_words, [2, 1, 1, 1])
        self.assertAlmostEqual(weighted_avg, 1)