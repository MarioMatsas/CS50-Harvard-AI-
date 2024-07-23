from collections import deque
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Go through all the variables
        for variable in self.domains:
            # Go through all the words in their respective domains
            for word in self.domains[variable]:
                # Remove the ones that don't match it's length
                if len(word) != variable.length:
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # Assume that no revesion takes place
        revision = False
        overlap = self.crossword.overlaps[x, y]
        if overlap is None:
            return revision
        
        overlap_x, overlap_y = overlap
        to_remove = set()
        for word_x in self.domains[x]:
            # Chec kif any words dont match at the overlap
            if not any(word_x[overlap_x] == word_y[overlap_y] for word_y in self.domains[y]):
                # Don't remove yet, just schedule the removal
                to_remove.add(word_x)
                revision = True
        
        self.domains[x] -= to_remove
        return revision

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = deque(arcs if arcs else [(x, y) for x in self.crossword.variables for y in self.crossword.neighbors(x) if x != y])
        while queue: # Queue not empty
            x, y = queue.popleft()
            re = self.revise(x, y)
            if re == False:
                continue
            else:
                if len(self.domains[x]) == 0:
                # No solution can be found
                    return False
                else:
                    # Since we removed something, we have to ensure the
                    # consisency with the rest of the neightboors
                    # since they might have relied on wha we removed
                    for neighbor in self.crossword.neighbors(x) - {y}:
                        queue.append((neighbor, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Check if all the variables are in the assignment
        return set(assignment.keys()) == set(self.crossword.variables)


    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Constraint 1) No same values 
        if len(set(assignment.values())) != len(assignment):
            return False
        
        for v1 in assignment:
            # Constraint 2) every value is the correct length
            if len(assignment[v1]) != v1.length:
                return False

            # Constraint 3) there are no conflicts between neighboring variables
            # Find v1's neighbors and check the overlap
            neighbors = self.crossword.neighbors(v1)
            for neighbor in neighbors:
                if neighbor in assignment:
                    overlap_v1, overlap_neigh = self.crossword.overlaps[v1, neighbor]
                    if assignment[v1][overlap_v1] != assignment[neighbor][overlap_neigh]:
                        return False
        return True


    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        eliminations_dict = {}
        neighbors = self.crossword.neighbors(var)
        for word in self.domains[var]:
            # Keep track of the total eliminations for each word in var's domain
            eliminations = 0
            for neighbor in neighbors:
                if neighbor not in assignment:
                    overlap_var, overlap_neigh = self.crossword.overlaps[var, neighbor]
                    # Go through all the neighbor's words and see how many dont match
                    for word_neigh in self.domains[neighbor]:
                        if word[overlap_var] != word_neigh[overlap_neigh]:
                            eliminations += 1
            eliminations_dict[word] = eliminations
        
        # Sort the words in var's domain based on the above eliminations, from fewest to most eliminations
        sorted_values = sorted(self.domains[var], key=lambda word: eliminations_dict[word])

        return sorted_values
            
    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Go through all the variables and find the ones that have the
        # least amount of values in their domain and dont belong to assignment
        fewest_values = float("inf")
        for variable in self.domains:
            if variable not in assignment:
                fewest_values = min(len(self.domains[variable]), fewest_values)
        candidate_vars = []
        for variable in self.domains:
            if variable not in assignment and len(self.domains[variable])==fewest_values:
                candidate_vars.append(variable)

        # If there is only one candidate, return it, otherwise advance to
        # he next huristic check
        if len(candidate_vars) == 1:
            return candidate_vars[0]
        else:
            max_neighbors = 0
            for candidate in candidate_vars:
                max_neighbors = max(len(self.crossword.neighbors(candidate)), max_neighbors)
            
            for candidate in candidate_vars:
                if len(self.crossword.neighbors(candidate)) == max_neighbors:
                    return candidate
        
        
                

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        if self.assignment_complete(assignment):
            return assignment
        else:
            variable = self.select_unassigned_variable(assignment)
            values = self.order_domain_values(variable, assignment)
            for value in values:
                assignment[variable] = value
                if self.consistent(assignment):
                    result = self.backtrack(assignment)
                    if result:
                        return result
            return None



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
