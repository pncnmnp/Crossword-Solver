# Crossword-Solver
<p align="center">
![Image of a crossword puzzle](https://github.com/pncnmnp/Crossword-Solver/blob/master/screenshots/newspaper.jpg)
</p>

This solver guesses the probable solutions based on the clues provided and uses a SMT solver to predict the result

## How does it work ?
[I have written a blogpost explaining the working of this crossword-solver.](https://pncnmnp.github.io/blogs/crossword-1.html)

## Structure
The project has 4 main files:
*  `words.py`: Uses Moby's thesaurus, gensim's glove-wiki-gigaword-100 and nltk's Wordnet to guess the solutions
* `words_offline.py`: Uses all-clues.bz2 to guess the solutions
* `solve.py`: Solves the crossword based on the solution stored in `clues.json` using a SMT solver (Z3)
* `schema.py`: This is where a user needs to enter the layout of the crossword

## How to run
To run `words_offline.py`, I highly recommend using [pypy](https://pypy.org/). 
There is a considerable difference in performance between PyPy and native python's implementation (`./corpus/all-clues.bz2` is a large file when uncompressed).
I have observed certain libraries like `nltk` work flawlessly with PyPy whereas `z3` has some issues.
Native python (default) works reasonably well with `words.py` and `solve.py`.

## Working
**Here is the format entered in `schema.py`**

<pre>
CROSSWORD_GRID = {
	"__ of bad news": {"start":(0, 1), "direction":"D", "length": 6},
	"Posture problem": {"start":(0, 3), "direction":"D", "length": 5},
	"Loads": {"start":(0, 4), "direction":"D", "length": 6},
	"Laundry appliance": {"start":(0, 5), "direction":"D", "length": 5},
	"Lectured": {"start":(1, 0), "direction":"D", "length": 5},
	"One who weeps": {"start":(1, 2), "direction":"D", "length": 5},
	"Grassy clump": {"start":(0, 3), "direction":"A", "length": 3},
	"Pie chart portion": {"start":(1, 0), "direction":"A", "length": 6},
	"\"Scary Movie,\" e.g.": {"start":(2, 0), "direction":"A", "length": 6},
	"Maryland's state bird": {"start":(3, 0), "direction":"A", "length": 6},
	"Something worth saving": {"start":(4, 0), "direction":"A", "length": 6},
	"\"To __ is human\"": {"start":(5, 0), "direction":"A", "length": 3}
}
</pre>

**Output (using `words_offline.py`)**

![Crossword Output](https://github.com/pncnmnp/Crossword-Solver/blob/master/screenshots/output-crossword.png)

### I am getting error running `solve.py`
If the error being faced is: `z3.z3types.Z3Exception: model is not available`, it is because a solution with the clues in `clues.json` does not exist!

This is usually seen when trying fetching solutions for clues from `words.py`. I recommend running with `words_offline.py` in such cases.

## Attribution
* For corpus attribution, see [`./corpus/README`](https://github.com/pncnmnp/Crossword-Solver/blob/master/corpus/README.txt)
* [Wikipedia's MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page): [Donate to Wikipedia](https://wikimediafoundation.org/support/)
* https://nlp.stanford.edu/projects/glove/
* The crossword image is by <a href="https://pixabay.com/users/stevepb-282134/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=412452">Steve Buissinne</a> from <a href="https://pixabay.com/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=412452">Pixabay</a>
