from nltk.corpus import wordnet as wn
from file_path import *

class Words():
	def __init__(self):
		pass

	def one_word_solution(self, one_word_clues, clues):
		fp = open(MOBY_PATH)
		moby_lines = fp.readlines()
		clue_mapping = dict()

		# splits and re-indexes clues such as 'extra-large' as 'large'
		# this is done to maintain consistency with 'one_word_clues'
		for word in clues:
			clues[word.replace("-", " ").split()[-1].lower()] = clues.pop(word)

		for line in moby_lines:
			guess_words = line.replace("\n", "").split(",")

			# removing spaces between the same word: at first -> atfirst
			guess_words = list(map(lambda word: word.replace(" ", ""), guess_words))
			common = list(set(guess_words).intersection(set(one_word_clues)))

			if len(common) == 0:
				continue
			else:
				for word in common:
					guess_words = [guess for guess in guess_words if len(guess)==clues[word]]
					try:
						clue_mapping[word] += guess_words
					except:
						clue_mapping[word] = guess_words

					clue_mapping[word] = sorted(list(set(clue_mapping[word])))	

		return clue_mapping

	def fetch_words(self, clues):
		"""	1. The tense of the clues have to be guessed
		    2. We segregate the "one word" clues with "sentence" clues
		    3. Possible solutions of the "one word" clues (in the tenses required)
		       are searched in Moby's Thesaurus
		    4. "Sentence" clues are searched in Wordnet (NLTK's version)
		    5. If a "sentence" clue has less confidence level than expected,
		       Wikipedia's MediaWiki API is used.
		    6. All the possible solutions are searched with the criteria:
		           Word length is same as required ||in the correct tense||

		    Param: clues - dict
		           {clue_1: word_len_1, clue_2: word_len_2}
		"""
		all_clues = list(clues.keys())
		one_word_clues = [clue.lower() for clue in all_clues if len(clue.split(" ")) == 1]

		# converting words such as extra-large into large
		one_word_clues += [clue.split("-")[-1].lower() for clue in all_clues 
								if ("-" in clue) and (len(clue.split("-"))) == 2]

		one_word_solved = self.one_word_solution(one_word_clues, clues)

if __name__ == '__main__':
	Words().fetch_words({"Rescue": 4, "Outmoded": 5, "Bound": 6, "Inflamed swelling on eyelid": 4, "Depth of six feet": 6})
