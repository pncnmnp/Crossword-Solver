from ast import literal_eval
from file_path import *
import json
import z3

"""
NOTE: No length-verification is required in Solve(),
      as all clues retrieved from CLUES_PATH are of required length
"""

# Pattern is (initial_X, initial_Y), direction(D or A), length
GRID = {
	"A type of cheese": {"start":(0, 7), "direction":"D", "length": 4},
	"Indian Grandmaster": {"start":(0, 11), "direction":"D", "length": 5},
	"A small european singing bird": {"start":(1, 7), "direction":"A", "length": 5},
	"A plant of the cabbage species": {"start":(2, 3), "direction":"D", "length": 8},
	"Director of Raging Bull": {"start":(3, 0), "direction":"A", "length": 8},
	"Fireplace": {"start":(5, 3), "direction":"A", "length": 7},
	"A popular game character created by Shigeru Miyamoto": {"start":(5, 6), "direction":"D", "length": 5},
	"Author who created Sherlock Holmes": {"start":(7, 8), "direction":"D", "length": 5},
	"The science of life": {"start":(9, 2), "direction":"A", "length": 7},
	"Used for baking or roasting": {"start":(11, 6), "direction":"A", "length": 4}
}

class Solve():
	def __init__(self):
		pass

	def fetch_clues(self):
		"""Fetches the clues present in "clues.json"
		"""
		clues = dict()
		with open(CLUES_PATH) as fp:
			clues = literal_eval(json.load(fp))
		return clues

	def get_matrix(self):
		clues = self.fetch_clues()
		start_positions = dict()

		# finding the square matrix size
		max_val = 0
		for clue in GRID:
			start_positions[GRID[clue]["start"]] = clue

			if GRID[clue]["start"][0] > max_val:
				max_val = GRID[clue]["start"][0]
			elif GRID[clue]["start"][1] > max_val:
				max_val = GRID[clue]["start"][1]

		# As the GRID starts from 0, we have to add 1 to get actual max_val
		max_val += 1

		matrix = [[None for index in range(max_val)] for index in range(max_val)]

		# The following code encodes the matrix declared with z3.Int(VALUE)
		# If at a position value is: (z3.Int(VALUE), z3.Int(VALUE)), it signifies intersection is taking place there
		for x_index in range(max_val):
			for y_index in range(max_val):
				if (x_index, y_index) in list(start_positions.keys()):
					pos_info = GRID[start_positions[(x_index, y_index)]]
					for i in range(pos_info["length"]):

						if pos_info["direction"] == "A":
							if isinstance(matrix[x_index][y_index + i], z3.z3.ArithRef):
								matrix[x_index][y_index + i] = (matrix[x_index][y_index + i], z3.Int("alpha_" + str(x_index) + "_" + str(y_index + i)))
							else:
								matrix[x_index][y_index + i] = z3.Int("alpha_" + str(x_index) + "_" + str(y_index + i))

						elif pos_info["direction"] == "D":
							if isinstance(matrix[x_index + i][y_index], z3.z3.ArithRef):
								matrix[x_index + i][y_index] = (matrix[x_index + i][y_index], z3.Int("alpha_" + str(x_index + i) + "_" + str(y_index)))
							else:
								matrix[x_index + i][y_index] = z3.Int("alpha_" + str(x_index + i) + "_" + str(y_index))

		return matrix

if __name__ == '__main__':
	pass
