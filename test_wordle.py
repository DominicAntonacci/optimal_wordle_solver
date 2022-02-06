"""
Unit tests for Wordle.

I prefer pytest, but am using unittest to avoid the dependency and ensure this works with PyPy.
"""
import unittest

from wordle import WordleInformation, get_guess_value, make_guess


class TestWordleInformation(unittest.TestCase):
    def assert_is_green(self, wi, idx, letter, min_num):
        """
        Does the correct assertion checks for a green tile.

        :param wi: The WordleInformation object.
        :param idx: The index to check.
        :param letter: The letter.
        :param min_num: The minimum number of occurances.
        """
        assert wi.possible_letters[idx] == set(letter)
        assert wi.minimum_letters[letter] == min_num
        if letter in wi.maximum_letters:
            assert wi.maximum_letters[letter] == min_num

    def assert_is_yellow(self, wi, idx, letter, min_num):
        """
        Does the correct assertion checks for a yellow tile.

        :param wi: The WordleInformation object.
        :param idx: The index to check.
        :param letter: The letter.
        :param min_num: The minimum number of occurances.
        """
        assert letter not in wi.possible_letters[idx]
        assert wi.minimum_letters[letter] == min_num
        if letter in wi.maximum_letters:
            assert wi.maximum_letters[letter] == min_num

    def assert_is_gray(self, wi, letter, max_num):
        """
        Does the correct assertion checks for a gray tile.

        :param wi: The WordleInformation object.
        :param letter: The letter.
        :param max_num: The maximum number of occurances.
        """
        if max_num == 0:
            for idx in range(5):
                assert letter not in wi.possible_letters[idx]

        assert wi.maximum_letters[letter] == max_num

        # The only way to get a gray tile is for the minimum to be fully
        # populated.
        if letter in wi.minimum_letters:
            assert wi.minimum_letters[letter] == max_num

    def test_constructor1(self):
        """
        Works through the first example on
        https://nerdschalk.com/wordle-same-letter-twice-rules-explained-how-does-it-work/
        verifying my results.

        In case the link goes bad, the true word is "abbey".
        """
        wi = WordleInformation(None, "opens", "--+--")

        def _check1(wi):
            for letter in "opns":
                self.assert_is_gray(wi, letter, 0)
            self.assert_is_yellow(wi, 2, "e", 1)

        _check1(wi)
        assert wi.is_valid_word("abbey")

        # Ensure duplication works
        wi = WordleInformation(wi, None, None)
        _check1(wi)
        assert wi.is_valid_word("abbey")

        # Test the second word.
        wi = WordleInformation(wi, "babes", "++==-")
        _check1(wi)

        def _check2(wi):
            self.assert_is_yellow(wi, 0, "b", 2)
            self.assert_is_yellow(wi, 1, "a", 1)
            self.assert_is_green(wi, 2, "b", 2)
            self.assert_is_green(wi, 3, "e", 1)
            self.assert_is_gray(wi, "s", 0)

        _check2(wi)
        assert wi.is_valid_word("abbey")

        # Test the third word.
        wi = WordleInformation(wi, "kebab", "-+=++")
        _check1(wi)
        _check2(wi)

        def _check3(wi):
            self.assert_is_gray(wi, "k", 0)
            self.assert_is_yellow(wi, 1, "e", 1)
            self.assert_is_green(wi, 2, "b", 2)
            self.assert_is_yellow(wi, 3, "a", 1)
            self.assert_is_yellow(wi, 4, "b", 2)

        _check3(wi)
        assert wi.is_valid_word("abbey")

        # Test the fourth word
        wi = WordleInformation(wi, "abyss", "==+--")
        _check1(wi)
        _check2(wi)
        _check3(wi)

        def _check4(wi):
            self.assert_is_green(wi, 0, "a", 1)
            self.assert_is_green(wi, 1, "b", 2)
            self.assert_is_yellow(wi, 2, "y", 1)
            self.assert_is_gray(wi, "s", 0)

        _check4(wi)
        assert wi.is_valid_word("abbey")

    def test_constructor2(self):
        """
        Works through the first example on
        https://nerdschalk.com/wordle-same-letter-twice-rules-explained-how-does-it-work/
        verifying my results.

        In case the link goes bad, the true word is "abbey".
        """
        wi = WordleInformation(None, "algae", "=---+")

        def _check1(wi):
            self.assert_is_green(wi, 0, "a", 1)
            self.assert_is_gray(wi, "l", 0)
            self.assert_is_gray(wi, "g", 0)
            self.assert_is_gray(wi, "a", 1)
            self.assert_is_yellow(wi, 4, "e", 1)

        _check1(wi)
        assert wi.is_valid_word("abbey")

        wi = WordleInformation(wi, "keeps", "-+---")
        _check1(wi)

        def _check2(wi):
            self.assert_is_gray(wi, "k", 0)
            self.assert_is_yellow(wi, 1, "e", 1)
            self.assert_is_gray(wi, "e", 1)
            self.assert_is_gray(wi, "p", 0)
            self.assert_is_gray(wi, "s", 0)

        _check2(wi)
        assert wi.is_valid_word("abbey")

        wi = WordleInformation(wi, "orbit", "--=--")
        _check1(wi)
        _check2(wi)

        def _check3(wi):
            self.assert_is_gray(wi, "o", 0)
            self.assert_is_gray(wi, "r", 0)
            self.assert_is_gray(wi, "i", 0)
            self.assert_is_gray(wi, "t", 0)

        # This check happens outside because "b" is updated in the next check.
        self.assert_is_green(wi, 2, "b", 1)
        _check3(wi)
        assert wi.is_valid_word("abbey")

        wi = WordleInformation(wi, "abate", "==--+")
        _check1(wi)
        _check2(wi)
        _check3(wi)

        def _check4(wi):
            self.assert_is_green(wi, 0, "a", 1)
            self.assert_is_green(wi, 2, "b", 2)
            self.assert_is_gray(wi, "a", 1)
            self.assert_is_gray(wi, "t", 0)
            self.assert_is_yellow(wi, 4, "e", 1)

        _check4(wi)
        assert wi.is_valid_word("abbey")

    def test_is_valid_word(self):
        """
        Poor man's unit test because I'm lazy.
        """
        wi = WordleInformation()

        # Check restricting letters
        wi.possible_letters = tuple(
            [
                set("abc"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("abcdefghijklmnopqrstuvwxyz"),
                set("xyz"),
            ]
        )
        assert not wi.is_valid_word("abcde")
        assert not wi.is_valid_word("xyzab")
        assert wi.is_valid_word("cabyz")

        # Check maximum letters
        wi.minimum_letters = {
            "z": 2,
            "e": 1,
        }
        assert not wi.is_valid_word("cabyz")
        assert not wi.is_valid_word("caeyz")
        assert not wi.is_valid_word("czbyz")
        assert wi.is_valid_word("czeyz")

        # Check maximum letters
        wi = WordleInformation()
        wi.maximum_letters = {
            "z": 0,
            "e": 1,
        }
        assert not wi.is_valid_word("cabyz")
        assert not wi.is_valid_word("abcee")
        assert wi.is_valid_word("abcde")

    def test_make_guess(self):
        assert make_guess("apple", "apexz") == "==--+"
        assert make_guess("apexz", "apple") == "==+--"
        assert make_guess("appep", "apple") == "===+-"

        # From https://nerdschalk.com/wordle-same-letter-twice-rules-explained-how-does-it-work/
        assert make_guess("opens", "abbey") == "--+--"
        assert make_guess("babes", "abbey") == "++==-"
        assert make_guess("kebab", "abbey") == "-+=++"
        assert make_guess("abyss", "abbey") == "==+--"
        assert make_guess("abbey", "abbey") == "====="
        assert make_guess("algae", "abbey") == "=---+"
        assert make_guess("keeps", "abbey") == "-+---"
        assert make_guess("orbit", "abbey") == "--=--"
        assert make_guess("abate", "abbey") == "==--+"

    def test_get_guess_value(self):
        """
        Tests get_guess_value.

        Guess/answer mappings.

        * grain/grain: ===== Score 0
        * grain/grown: ==--= Score 1 (only grown remaining)
        * grain/stews: ----- Score 2 (stews/weeds remaining)
        * grain/weeds: ----- Score 2 (stews/weeds remaining)
        """
        guess = "grain"
        possible_words = ["grain", "grown", "stews", "weeds"]

        avg = get_guess_value(guess, possible_words)
        self.assertAlmostEqual(avg, 5 / 4)

        weighted_avg = get_guess_value(guess, possible_words, [2, 1, 1, 1])
        self.assertAlmostEqual(weighted_avg, 1)
