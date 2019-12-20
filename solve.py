from ast import literal_eval
from tabulate import tabulate
from file_path import *
import json
import z3
from schema import CROSSWORD_GRID

"""
NOTE: No length-verification is required in Solve(),
      as all clues retrieved from CLUES_PATH are of required length
"""

# Pattern is (initial_X, initial_Y), direction(D or A), length
# "": {"start":(), "direction":"", "length": },
GRID = CROSSWORD_GRID

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
		# If at a position value is: (z3.Int(VALUE)_1, z3.Int(VALUE)_2), it signifies intersection is taking place there
		# NOTE: _1 -> signifies the COLUMN index AND _2 -> signifies the ROW index
		for x_index in range(max_val):
			for y_index in range(max_val):

				if (x_index, y_index) in list(start_positions.keys()):
					pos_info = GRID[start_positions[(x_index, y_index)]]
					for i in range(pos_info["length"]):

						if pos_info["direction"] == "A":
							if isinstance(matrix[x_index][y_index + i], z3.z3.ArithRef):
								matrix[x_index][y_index + i] = (z3.Int("alpha_" + str(x_index) + "_" + str(y_index + i) + "_1"), z3.Int("alpha_" + str(x_index) + "_" + str(y_index + i) + "_2"))
							else:
								matrix[x_index][y_index + i] = z3.Int("alpha_" + str(x_index) + "_" + str(y_index + i))

						elif pos_info["direction"] == "D":
							if isinstance(matrix[x_index + i][y_index], z3.z3.ArithRef):
								matrix[x_index + i][y_index] = (z3.Int("alpha_" + str(x_index + i) + "_" + str(y_index) + "_1"), z3.Int("alpha_" + str(x_index + i) + "_" + str(y_index) + "_2"))
							else:
								matrix[x_index + i][y_index] = z3.Int("alpha_" + str(x_index + i) + "_" + str(y_index))

		return matrix, start_positions, max_val

	def convert_clues_code(self):
		"""converts all the clues (in string format) to a list of their ascii characters value
		   example: "mumbai" -> [109, 117, 109, 98, 97, 105]
		"""
		clues = self.fetch_clues()
		clues_ord = dict()

		for clue in clues:
			for guess in clues[clue]:
				try:
					clues_ord[clue].append([ord(ch) for ch in guess.lower()])
				except:
					clues_ord[clue] = [[ord(ch) for ch in guess.lower()]]

		return clues_ord

	def make_guess_constraint(self):
		clues = self.convert_clues_code()
		matrix, start_positions, max_val = self.get_matrix()

		clue_constraint = list()

		for x_index in range(max_val):
			for y_index in range(max_val):
				if (x_index, y_index) in list(start_positions.keys()):
					pos_info = GRID[start_positions[(x_index, y_index)]]
					clue = start_positions[(x_index, y_index)]

					guesses_ord = clues[clue]
					all_guesses_constraint = list()

					for guess_ord in guesses_ord:
						guess_constraint = list()
						x_i = x_index
						y_i = y_index

						for ch in guess_ord:
							if isinstance(matrix[x_i][y_i], tuple):
								# NOTE: _1 -> signifies the COLUMN index AND _2 -> signifies the ROW index
								if pos_info["direction"] == "D":
									matrix_val = matrix[x_i][y_i][0]
								elif pos_info["direction"] == "A":
									matrix_val = matrix[x_i][y_i][1]
							else:
								matrix_val = matrix[x_i][y_i]

							guess_constraint.append(z3.And(matrix_val == ch))

							if pos_info["direction"] == "D":
								x_i += 1
							elif pos_info["direction"] == "A":
								y_i += 1

						all_guesses_constraint.append(z3.And(guess_constraint))

					clue_constraint.append(z3.Or(all_guesses_constraint))

		clues_constraint = z3.And(clue_constraint)

		return clues_constraint

	def common_position_constraint(self):
		clues = self.convert_clues_code()
		matrix, start_positions, max_val = self.get_matrix()

		equality_constraint = list()

		for x_index in range(max_val):
			for y_index in range(max_val):
				if isinstance(matrix[x_index][y_index], tuple):
					first = matrix[x_index][y_index][0]
					second = matrix[x_index][y_index][1]

					equality_constraint.append(z3.And(first == second))

		common_position_constraint = z3.And(equality_constraint)

		return common_position_constraint

	def apply_constraints(self):
		solver = z3.Solver()
		solver.add(self.make_guess_constraint())
		solver.add(self.common_position_constraint())
		solver.check()
		
		return solver.model()

	def solution(self):
		solved = self.apply_constraints()
		solved_keys = [index.name() for index in solved]
		matrix, start_positions, max_val = self.get_matrix()

		for x_index in range(max_val):
			for y_index in range(max_val):
				if isinstance(matrix[x_index][y_index], tuple):
					matrix_val = matrix[x_index][y_index][0]
				elif matrix[x_index][y_index] != None:
					matrix_val = matrix[x_index][y_index]
				else:
					continue

				no = solved[matrix_val]
				ch = chr(no.as_long())
				matrix[x_index][y_index] = ch

		return matrix

if __name__ == '__main__':
	solve = Solve()
	print(tabulate(solve.solution()))
