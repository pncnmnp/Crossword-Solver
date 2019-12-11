from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from ast import literal_eval
import gensim.downloader as api
from file_path import *
import pickle
import string
import requests

class Words():
	def __init__(self):
		pass

	def fetch_all_word_vectors(self):
		return api.load("glove-wiki-gigaword-100")

	def store_all_word_vectors(self):
		all_word_vectors = self.fetch_all_word_vectors()
		with open(ALL_WORD_VECTOR_PATH, "wb") as fp:
			pickle.dump(all_word_vectors, fp)

	def retrieve_all_word_vectors(self):
		try:
			with open(ALL_WORD_VECTOR_PATH, "rb") as fp:
				all_word_vectors = pickle.load(fp)
			return all_word_vectors
		except:
			return None		

	def wikipedia_solution(self, wikipedia_clues, clues):
		WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php?action=query&utf8=&format=json&list=search&srsearch="
		stop = stopwords.words('english') + list(string.punctuation)
		clue_mapping = dict()

		for sentence in wikipedia_clues:
			req = requests.get(WIKIPEDIA_API + sentence)
			wiki_json = literal_eval(req.text)

			# The following code finds all titles from the JSON response,
			# The title is stripped of stop_words and punctuations
			# The title is split by space
			# Duplicates are removed and words are converted to a 1-D list
			solutions = list(set([word for word in [[word for word in word_tokenize(info["title"].lower()) if word not in stop] for info in wiki_json["query"]["search"]] for word in word]))

			for soln in solutions:
				if len(soln) != clues[sentence]:
					continue
				try:
					clue_mapping[sentence] += [soln]
				except:
					clue_mapping[sentence] = [soln]

		return clue_mapping

	def sentence_solution(self, sentence_clues, clues):
		"""ADD SIZES
		"""
		all_words_wordnet = wn.words()

		word_vectors = self.retrieve_all_word_vectors()
		if word_vectors == None:
			self.store_all_word_vectors()
			word_vectors = self.retrieve_all_word_vectors()

		stop = stopwords.words('english') + list(string.punctuation)
		clues_tokenized = dict()
		clue_mapping = dict()


		# Tokenize all the clues, removing stopwords and punctuations
		for clue in sentence_clues:
			tokenized = [word for word in word_tokenize(clue.lower()) if word not in stop]
			clues_tokenized[clue] = tokenized

		print("STARTING FETCH.....")
		for word_wordnet in all_words_wordnet:
			iter_val = len(wn.synsets(word_wordnet))

			for syn_no in range(iter_val):
				synset_tokenized = [word for word in word_tokenize(wn.synsets(word_wordnet)[syn_no].definition().lower()) if word not in stop]

				for clue in sentence_clues:
					if len(word_wordnet) != clues[clue]:
						continue
					try:
						similarity = word_vectors.n_similarity(clues_tokenized[clue], synset_tokenized)
					except KeyError as e:
						try:
							# This error is caused by word_vectors.n_similarity()
							# The keyerror is printed as "word 'XXX' not in vocabulary"
							# We are giving the prediction another chance by removing the KeyError word
							try_removing_a_word = e.args[0].replace("word ", "").replace("not in vocabulary", "").replace("'", "").strip()
							synset_tokenized.remove(try_removing_a_word)
							similarity = word_vectors.n_similarity(clues_tokenized[clue], synset_tokenized)
						except:
							continue
					except:
						continue

					if similarity > 0.65:
						try:
							clue_mapping[clue] += [(word_wordnet, similarity)]
						except:
							clue_mapping[clue] = [(word_wordnet, similarity)]
						clue_mapping[clue] = sorted(set(clue_mapping[clue]), key=lambda x: x[1], reverse=True)

		return clue_mapping

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
		# one_word_solved = self.one_word_solution(one_word_clues, clues)

		sentence_clues = list(set(all_clues).difference(set(one_word_clues)))
		sentence_solved = self.sentence_solution(sentence_clues, clues)

		wikipedia_clues = list()
		# Print top 10 results 
		# And identify clues which require a Wikipedia fetch
		for clue in sentence_solved:
			sentence_solved[clue] = sentence_solved[clue][:10]
			if len(sentence_solved[clue]) < 10 or sentence_solved[clue][0][1] < 0.69:
				wikipedia_clues.append(clue)

		wikipedia_solved = self.wikipedia_solution(wikipedia_clues, clues)
		print(wikipedia_solved)

if __name__ == '__main__':
	# Words().fetch_words({"Rescue": 4, "Outmoded": 5, "Bound": 6, "Inflamed swelling on eyelid": 4, "Depth of six feet": 6})
	Words().fetch_words({"Russian liquor": 5, "Lebanese capital": 6, "Coiled fossil": 8, "Inflamed swelling on eyelid": 4, "Depth of six feet": 6, "Opera composer": 7, "Young cat": 6, "Barnaby ___, Dickens novel": 5, "Fair-haired": 6})
