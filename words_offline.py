from nltk.corpus import stopwords
from collections import Counter
from schema import CROSSWORD_GRID
from file_path import *
import string
import math
import re
import json

class Words_Offline():
	def __init__(self):
		pass

	def all_solution(self, clues):
		stop = stopwords.words('english') + [""]

		with open(ALL_CLUES, encoding="latin-1") as fp:
			dict_guesses = fp.readlines()

		clue_mapping = dict()
		all_lengths = []
		for clue in clues:
			clue_mapping[clue] = list()
			if clues[clue] not in all_lengths:
				all_lengths.append(clues[clue])

		clue_statements = list(clues.keys())
		clue_vecs = dict()
		for clue in clue_statements:
			clue_vecs[clue] = [word for word in [word.strip(string.punctuation) for word in clue.lower().split()] if word not in stop]

		print(">>> STARTING ALL CLUES FETCH (V.1).....")
		for guess in dict_guesses:
			if len(guess.split()[0]) not in all_lengths:
				continue

			guess_statement = " ".join(guess.split()[4:])
			guess_vec = Counter([word for word in [word.strip(string.punctuation) for word in guess_statement.lower().split()] if word not in stop])

			for clue in clue_statements:
				if len(guess.split()[0]) == clues[clue]:
					clue_vec = Counter(clue_vecs[clue])

					# https://stackoverflow.com/questions/15173225/calculate-cosine-similarity-given-2-sentence-strings
					intersection = set(guess_vec.keys()) & set(clue_vec.keys())
					numerator = sum([guess_vec[x] * clue_vec[x] for x in intersection])

					sum1 = sum([guess_vec[x]**2 for x in guess_vec.keys()])
					sum2 = sum([clue_vec[x]**2 for x in clue_vec.keys()])
					denominator = math.sqrt(sum1) * math.sqrt(sum2)

					if not denominator:
						sim =  0.0
					else:
						sim = float(numerator) / denominator

					if sim > 0.65:
						clue_mapping[clue] += [guess.split()[0].lower()]

		for clue in clues:
			clue_mapping[clue] = list(set(clue_mapping[clue]))				

		return clue_mapping

	def fetch_words(self, clues):
		all_solved = self.all_solution(clues)
		print(">>> STORED CLUES.....")
		with open(CLUES_PATH, "w") as fp:
			json.dump(str(all_solved), fp)

if __name__ == '__main__':
	grid = CROSSWORD_GRID
	clues = dict()
	for clue in CROSSWORD_GRID:
		clues[clue] = CROSSWORD_GRID[clue]["length"]

	Words_Offline().fetch_words(clues)
