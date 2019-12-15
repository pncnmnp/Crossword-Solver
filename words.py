from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from ast import literal_eval
import gensim.downloader as api
from file_path import *
import pickle
import string
import requests
import inflect # Library used to check whether a sentence is singular or plural
import json

"""
TODO: >> Plural detection and conversion [done]
      >> Variable cutoff value
"""

class Words():
	def __init__(self):
		self.word_vectors = self.retrieve_all_word_vectors()
		if self.word_vectors == None:
			self.store_all_word_vectors()
			self.word_vectors = self.retrieve_all_word_vectors()

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
		WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php?action=query&utf8=&format=json&list=search&srlimit=50&srsearch="
		stop = stopwords.words('english') + list(string.punctuation)
		clue_mapping = dict()

		print(">>> STARTING WIKI FETCH.....")
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

	def reduce_search_bound(self, all_words_wordnet, sentence_clues, clues):
		"""Reduces the search space by finding most similar words from self.word_vectors
		   using the method 'most_similar'.
		   Common words found between self.word_vectors.most_similar() and all_words_wordnet
		   are returned.
		   Param: all_words_wordnet : has to be wn.words()
		                              where wn is wordnet from nltk.corpus
		"""
		words = list(all_words_wordnet)
		possible_words = list()
		stop = stopwords.words('english') + list(string.punctuation)
		topn = 4000

		for sentence in sentence_clues:
			pos = [word for word in word_tokenize(sentence.lower()) if word not in stop]
			search_words = [word[0] for word in self.word_vectors.most_similar(positive=pos, topn=topn) if len(word[0])==clues[sentence]]
			possible_words += list(set(words).intersection(set(search_words)))

		return sorted(list(set(possible_words)))

	def sentence_solution(self, sentence_clues, clues):
		all_words_wordnet = self.reduce_search_bound(wn.words(), sentence_clues, clues)

		word_vectors = self.word_vectors

		stop = stopwords.words('english') + list(string.punctuation)
		clues_tokenized = dict()
		clue_mapping = dict()
		
		clue_plural = dict()
		infl = inflect.engine()

		# Tokenize all the clues, removing stopwords and punctuations
		for clue in sentence_clues:
			tokenized = [word for word in word_tokenize(clue.lower()) if word not in stop]
			clues_tokenized[clue] = tokenized

			# check if the clue is singular or plural
			if infl.singular_noun(clue) == False:
				clue_plural[clue] = "singular"
			else:
				clue_plural[clue] = "plural"

		print(">>> STARTING SENTENCE LOCAL FETCH.....")
		for word_wordnet in all_words_wordnet:
			iter_val = len(wn.synsets(word_wordnet))

			for syn_no in range(iter_val):
				synset_tokenized = [word for word in word_tokenize(wn.synsets(word_wordnet)[syn_no].definition().lower()) if word not in stop]

				for clue in sentence_clues:
					# To prevent any modifications on original variable
					# Can be caused if the clue is in plural form, and word_wordnet gets converted to plural form
					# This happens if length of the plural form of word matches with clue's required length
					# Example: "Young mares" (PLURAL) (length - 7) -> filly -> fillies
					temp_word_wordnet = word_wordnet

					if len(temp_word_wordnet) != clues[clue]:
						# Check if the plural form of the word is of same length as required by the crossword
						if clue_plural[clue] == "plural" and len(infl.plural(temp_word_wordnet)) == clues[clue]:
							temp_word_wordnet = infl.plural(temp_word_wordnet)
						else:
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
							clue_mapping[clue] += [(temp_word_wordnet, similarity)]
						except:
							clue_mapping[clue] = [(temp_word_wordnet, similarity)]
						clue_mapping[clue] = sorted(set(clue_mapping[clue]), key=lambda x: x[1], reverse=True)

		return clue_mapping

	def one_word_solution(self, one_word_clues, clues):
		fp = open(MOBY_PATH)
		moby_lines = fp.readlines()
		clue_mapping = dict()

		# Copy the contents of the 'clues' dict in a temp variable
		# To prevent any modification changes appearing globally
		temp_clues = dict()
		for word in list(clues.keys()):
			temp_clues[word] = clues[word]

		print(">>> STARTING ONE-WORD LOCAL FETCH (V.1).....")
		# splits and re-indexes clues such as 'extra-large' as 'large'
		# this is done to maintain consistency with 'one_word_clues'
		for word in list(temp_clues.keys()):
			temp_clues[word.replace("-", " ").split()[-1].lower()] = temp_clues.pop(word)

		for line in moby_lines:
			guess_words = line.replace("\n", "").split(",")

			# removing spaces between the same word: at first -> atfirst
			guess_words = list(map(lambda word: word.replace(" ", ""), guess_words))
			common = list(set(guess_words).intersection(set(one_word_clues)))

			if len(common) == 0:
				continue
			else:
				for word in common:
					guess_words = [guess for guess in guess_words if len(guess)==temp_clues[word]]
					try:
						clue_mapping[word] += guess_words
					except:
						clue_mapping[word] = guess_words

					clue_mapping[word] = sorted(list(set(clue_mapping[word])))

		return clue_mapping

	def one_word_solution_alternate(self, one_word_clues, clues):
		clue_mapping = dict()
		stop = stopwords.words('english') + list(string.punctuation)

		# For common words, optimal is around 100, for proper nouns optimal is 1000-2000
		topn = 100

		# Copy the contents of the 'clues' dict in a temp variable
		# To prevent any modification changes appearing globally
		temp_clues = dict()
		for word in list(clues.keys()):
			temp_clues[word] = clues[word]

		print(">>> STARTING ONE-WORD LOCAL FETCH (V.2).....")
		# splits and re-indexes clues such as 'extra-large' as 'large'
		# this is done to maintain consistency with 'one_word_clues'
		for word in list(temp_clues.keys()):
			temp_clues[word.replace("-", " ").split()[-1].lower()] = temp_clues.pop(word)

		for clue in one_word_clues:
			pos = [word for word in word_tokenize(clue.lower()) if word not in stop]
			clue_mapping[clue] = [word[0] for word in self.word_vectors.most_similar(positive=pos, topn=topn) if len(word[0]) == temp_clues[clue]]

		return clue_mapping

	def store_words(self, one_word_solved, one_word_clues, sentence_solved, wikipedia_solved):
		clues = dict()

		for key in list(one_word_solved.keys()):
			actual_key = [val[1] for val in one_word_clues if val[0]==key][0]
			try:
				clues[actual_key] += one_word_solved[key]
			except:
				clues[actual_key] = list()
				clues[actual_key] += one_word_solved[key]

		for key in list(sentence_solved.keys()):
			try:
				clues[key] += [word[0] for word in sentence_solved[key]]
				clues[key] += wikipedia_solved[key]
			except:
				clues[key] = list()
				clues[key] += [word[0] for word in sentence_solved[key]]
				clues[key] += wikipedia_solved[key]

		print(">>> STORED CLUES.....")
		with open(CLUES_PATH, "w") as fp:
			json.dump(str(clues), fp)

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
		one_word_clues = [(clue.lower(),clue) for clue in all_clues if len(clue.split(" ")) == 1]

		# converting words such as extra-large into large
		one_word_clues += [(clue.split("-")[-1].lower(),clue) for clue in all_clues 
								if ("-" in clue) and (len(clue.split("-"))) == 2]
		one_word_solved = self.one_word_solution_alternate([clue[0] for clue in one_word_clues], clues)

		sentence_clues = list(set(all_clues).difference(set(one_word_clues)))
		sentence_solved = self.sentence_solution(sentence_clues, clues)

		wikipedia_clues = list()
		# Print top N results
		N = 40
		for clue in sentence_solved:
			sentence_solved[clue] = sentence_solved[clue][:N]

		wikipedia_solved = self.wikipedia_solution(sentence_clues, clues)

		self.store_words(one_word_solved, one_word_clues, sentence_solved, wikipedia_solved)

if __name__ == '__main__':
	# THE WORDS INSERTED SHOULD HAVE THEIR STARTING LETTER CAPITALIZED
	Words().fetch_words({"A type of cheese": 4, "Indian Grandmaster": 5, "A small european singing bird": 5, "A plant of the cabbage species": 8, "Director of Raging Bull": 8, "Fireplace": 7, "A popular game character created by Shigeru Miyamoto": 5, "Author who created Sherlock Holmes": 5, "The science of life": 7, "Used for baking or roasting": 4})
