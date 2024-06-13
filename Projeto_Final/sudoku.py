import time
from collections import deque
import random


class Sudoku:
    def __init__(self, sudoku, base_delay=0.01, interval=10, threshold=5):
        self.grid = sudoku
        self.recent_requests = deque()
        self.base_delay = base_delay
        self.interval = interval
        self.threshold = threshold

    def _limit_calls(self, base_delay=0.01, interval=10, threshold=5):
        """Limit the number of requests made to the Sudoku object."""
        if base_delay is None:
            base_delay = self.base_delay
        if interval is None:
            interval = self.interval
        if threshold is None:
            threshold = self.threshold

        current_time = time.time()
        self.recent_requests.append(current_time)
        num_requests = len(
            [t for t in self.recent_requests if current_time - t < interval]
        )

        if num_requests > threshold:
            delay = base_delay * (num_requests - threshold + 1)
            time.sleep(delay)

    def __str__(self):
        string_representation = "| - - - - - - - - - - - |\n"

        for i in range(9):
            string_representation += "| "
            for j in range(9):
                string_representation += (
                    str(self.grid[i][j])
                    if self.grid[i][j] != 0
                    else f"\033[93m{self.grid[i][j]}\033[0m"
                )
                string_representation += " | " if j % 3 == 2 else " "

            if i % 3 == 2:
                string_representation += "\n| - - - - - - - - - - - |"
            string_representation += "\n"

        return string_representation

    def update_row(self, row, values):
        """Update the values of the given row."""
        self.grid[row] = values
    
    def update_column(self, col, values):
        """Update the values of the given column."""
        for row in range(9):
            self.grid[row][col] = values[row]

    def check_is_valid(
        self, row, col, num, base_delay=None, interval=None, threshold=None
    ):
        """Check if 'num' is not in the current row, column and 3x3 sub-box."""
        self._limit_calls(base_delay, interval, threshold)

        # Check if the number is in the given row or column
        for i in range(9):
            if self.grid[row][i] == num or self.grid[i][col] == num:
                return False

        # Check if the number is in the 3x3 sub-box
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.grid[start_row + i][start_col + j] == num:
                    return False

        return True

    def check_row(self, row, base_delay=None, interval=None, threshold=None):
        """Check if the given row is correct."""
        self._limit_calls(base_delay, interval, threshold)

        # Check row
        if sum(self.grid[row]) != 45 or len(set(self.grid[row])) != 9:
            return False

        return True

    def check_column(self, col, base_delay=None, interval=None, threshold=None):
        """Check if the given row is correct."""
        self._limit_calls(base_delay, interval, threshold)

        # Check col
        if (
            sum([self.grid[row][col] for row in range(9)]) != 45
            or len(set([self.grid[row][col] for row in range(9)])) != 9
        ):
            return False
        return True

    def check_square(self, row, col, base_delay=None, interval=None, threshold=None):
        """Check if the given 3x3 square is correct."""
        self._limit_calls(base_delay, interval, threshold)

        # Check square
        if (
            sum([self.grid[row + i][col + j] for i in range(3) for j in range(3)]) != 45
            or len(
                set([self.grid[row + i][col + j] for i in range(3) for j in range(3)])
            )
            != 9
        ):
            return False

        return True

    def check(self, base_delay=None, interval=None, threshold=None):
        """Check if the given Sudoku solution is correct.
        
        You MUST incorporate this method without modifications into your final solution.
        """
        
        for row in range(9):
            if not self.check_row(row, base_delay, interval, threshold):
                return False

        # Check columns
        for col in range(9):
            if not self.check_column(col, base_delay, interval, threshold):
                return False

        # Check 3x3 squares
        for i in range(3):
            for j in range(3):
                if not self.check_square(i*3, j*3, base_delay, interval, threshold):
                    return False

        return True
        
    def find_empty(self, grid):
        """Find an empty cell in the Sudoku puzzle."""
        lines = len(grid)
        columns = len(grid[0])

        for i in range(lines):
            for j in range(columns):
                if grid[i][j] == 0:
                    return (i, j)
        return None
    
    def empty_coords(self):
        stop = False
        empty_lst = []
        while not stop:
            empty = self.find_empty(self.grid)
            if empty is None:
                stop = True
            else:
                self.grid[empty[0]][empty[1]] = 1
                empty_lst.append(empty)
        for coord in empty_lst:
            self.grid[coord[0]][coord[1]] = 0
        return empty_lst
    
    def possible_values_by_row(self):
        values = []
        for i in range(9):
            numbers = [1,2,3,4,5,6,7,8,9]
            for j in range(9):
                if self.grid[i][j] in numbers:
                    numbers.remove(self.grid[i][j])
            values.append(numbers)
        return values

    def solve_sudoku(self,coords,num_validations=0):
        """Solve the Sudoku puzzle."""
        print("Solving the Sudoku puzzle...")
        numbers = self.possible_values_by_row()
        stop = False
        while not stop:
            for coord in coords:
                nums = numbers[coord[0]]
                self.grid[coord[0]][coord[1]] = random.choice(nums)
            num_validations += 1
            if self.check():
                print("entrou")
                stop = True    
        return self.grid,num_validations

    def minicheck_is_valid(self, row, col, num, base_delay=None, interval=None, threshold=None):
        """Check if 'num' is not in the current row and column. The sudoku might not have 9 lines."""
        self._limit_calls(base_delay, interval, threshold)

        # Check if the number is in the given row or column
        number_of_lines = len(self.grid)
        number_of_columns = len(self.grid[0])

        for i in range(number_of_lines):
            if i != row and self.grid[i][col] == num:
                return False

        for i in range(number_of_columns):
            if i != col and self.grid[row][i] == num:
                return False

        return True
if __name__ == "__main__":

    sudoku = Sudoku([[1, 6, 3, 8, 9, 2, 7, 5, 4], [8, 5, 2, 7, 4, 1, 9, 6, 3], [7, 4, 9, 5, 3, 6, 2, 8, 1], [9, 8, 7, 2, 5, 4, 3, 1, 6], [5, 2, 6, 1, 7, 3, 4, 9, 8], [3, 1, 4, 9, 6, 8, 5, 7, 2], [6, 9, 1, 4, 2, 5, 8, 3, 7], [4, 7, 8, 3, 1, 9, 6, 2, 5], [2, 3, 5, 6, 8, 7, 1, 4, 9]])

    print(sudoku)
    
    if sudoku.check():
        print("Sudoku is correct!")
    else:
        print("Sudoku is incorrect! Please check your solution.")
