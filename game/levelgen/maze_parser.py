"""Maze parser from the maze generator result."""
from enum import IntEnum
from typing import Dict, List, Set, Tuple


class Position(IntEnum):
    """Positions for (width, height) format."""
    WIDTH = 0
    HEIGHT = 1


class MazeData:
    """Stores the information of the maze.

    Attributes:
        width: the number of cells in the width.
        height: the number of cells in the height.
        cells:
            The 2D array (height) (width) with cells as
            byte (West South East North) with North as LSD
            with 0 open and 1 closed.
        start:
            The starting cell position with keys (width height).
        end:
            The ending cell position with keys (width height).
    """
    def __init__(self,
                 width: int, height: int,
                 cells: List[List[int]],
                 start: Dict[Position, int], end: Dict[Position, int],
                 path: Set[Tuple[int, int]]) -> None:
        self._width = width
        self._height = height
        self._cells = cells
        self._start = start
        self._end = end
        self._path = path

    @property
    def width(self) -> int:
        """Number of cells in the width"""
        return self._width

    @property
    def height(self) -> int:
        """Number of cells in the height"""
        return self._height

    def get_cell_int(self, width_pos: int, height_pos: int) -> int:
        """Returns the cell at the position width and height.

        Args:
            width_pos: the width position of the cell.
            height_pos: the height position of the cell.

        Returns:
            Returns the cell at the position in int format.
        """
        return self._cells[height_pos][width_pos]

    def is_start(self, width_pos: int, height_pos: int) -> bool:
        """Returns True if the starting cell is the position, False otherwise.

        Args:
            width_pos: the width position of the cell.
            height_pos: the height position of the cell.

        Returns:
            Returns True if the starting cell is the position, False otherwise.
        """
        return (self._start[Position.WIDTH] == width_pos
                and self._start[Position.HEIGHT] == height_pos)

    def is_end(self, width_pos: int, height_pos: int) -> bool:
        """Returns True if the ending cell is the position, False otherwise.

        Args:
            width_pos: the width position of the cell.
            height_pos: the height position of the cell.

        Returns:
            Returns True if the ending cell is the position, False otherwise.
        """
        return (self._end[Position.WIDTH] == width_pos
                and self._end[Position.HEIGHT] == height_pos)

    def is_in_path(self, width_pos: int, height_pos: int) -> bool:
        """Returns True if the position is in the solution, False otherwise.

        Args:
            width_pos: the width position of the cell.
            height_pos: the height position of the cell.

        Returns:
            Returns True if the position is in the solution, False otherwise.
        """
        return (width_pos, height_pos) in self._path


class MazeParser:
    """Parser for the maze in text format.
    """
    @staticmethod
    def parse(maze: str) -> MazeData:
        """Parse the maze in text format and returns a MazeData.

        Args:
            maze: the maze in string format.

        Returns:
            Returns MazeData with data from the maze text.

        Raises:
            ValueError: If the maze text is invalid.
        """
        def extract_width_height(maze_split: List[str]) -> Tuple[int, int]:
            """Returns the number of cells in width and height.

            Args:
                maze_split: the maze in text split by line.

            Returns:
                Returns the tuple (width, height).

            Raises:
                ValueError:
                    No line for maze.
                    No row for maze.
                    Inconsistant number of rows per line.
            """
            height = len(maze_split) - 4
            if height <= 0:
                raise ValueError("The maze does not exist (no line for maze)")
            width = len(maze_split[0])
            if width == 0:
                raise ValueError("The maze does not exist (no row for maze)")
            for line_idx in range(height):
                if width != len(maze_split[line_idx]):
                    raise ValueError(f"The maze width is inconsistant:"
                                     f" first width {width},"
                                     f" found {len(maze_split[line_idx])}"
                                     f" at line {line_idx + 1}")
            return width, height

        def extract_cells(maze_split: List[str]) -> List[List[int]]:
            """Returns the cells in 2D array from the maze in text format.

            Args:
                maze_split: the maze in text split by line.

            Returns:
                Returns a 2D array (height) (width) with cells as
                byte (West South East North) with North as LSD
                with 0 open and 1 closed.

            Raises:
                ValueError:
                    Invalid hex in maze.
            """
            cells: List[List[int]] = list()
            hexadecimals = {letter: number
                            for number, letter
                            in enumerate("0123456789ABCDEF")}
            for line in maze_split[:-4]:
                cells_line: List[int] = list()
                for letter in line:
                    if letter in hexadecimals:
                        letter_int = hexadecimals[letter]
                        cells_line.append(letter_int)
                    else:
                        ValueError(f"Invalid hex in maze: {letter}")
                cells.append(cells_line)
            return cells

        def check_newline(maze_split: List[str]) -> None:
            """Checks the mandatory empty newline is present.

            Args:
                maze_split: the maze in text split by line.

            Raises:
                ValueError:
                    No mandatory empty newline at it position.
            """
            if maze_split[-4] != "":
                raise ValueError("No space between maze and start")

        def extract_positions(maze_split: List[str],
                              width: int, height: int) -> Tuple[
                                  Dict[Position, int], Dict[Position, int]]:
            """Returns the positions of the starting cell and the ending cell.

            Args:
                maze_split: the maze in text split by line.
                width: the number of cells in the width.
                height: the number of cells in the height.

            Returns:
                Returns a tuple (start, end)
                with each as dict with keys (width height)
                with their associated values.

            Raises:
                ValueError:
                    Start or end out of bound.
            """
            def extract_position(position_str: str,
                                 position_type: str) -> Dict[Position, int]:
                """Extract one position.

                Args:
                    position_str: the format in string of a position
                    position_type: the name of the position

                Returns:
                    Returns a position as dict with keys (width height)
                    with their associated values

                Raises:
                    ValueError:
                        Position name out of bound.
                """
                pos_width, pos_height = position_str.split(",")
                pos = {Position.WIDTH: int(pos_width),
                       Position.HEIGHT: int(pos_height)}
                if (pos[Position.WIDTH] < 0 or pos[Position.WIDTH] >= width
                        or pos[Position.HEIGHT] < 0
                        or pos[Position.HEIGHT] >= height):
                    raise ValueError(f"Invalid {position_type}"
                                     f" {pos[Position.WIDTH]},"
                                     f" {pos[Position.HEIGHT]}"
                                     f" for {width}, {height}")
                return pos

            return (extract_position(maze_split[-3], "start"),
                    extract_position(maze_split[-2], "end"))

        def extract_path(maze_split: List[str],
                         start: Dict[Position, int],
                         end: Dict[Position, int],
                         max_width: int,
                         max_height: int) -> Set[Tuple[int, int]]:
            """Returns each position in the solution path.

            Args:
                maze_split: the maze in text split by line.
                start: the starting position.
                end: the ending position.
                max_width: the number of cells in the width.
                max_height: the number of cells in the height.

            Returns:
                Returns a set of each position (width, height).

            Raises:
                ValueError:
                    Invalid path value.
                    Invalid path: Out of maze bound.
                    Invalid path: No at the ending position using the path.
            """
            path = maze_split[-1]
            for letter in path:
                if letter not in "NESW":
                    raise ValueError(f"Invalid path value: {letter}")
            cells_in_path = set()
            current_width_pos, current_height_pos = (start[Position.WIDTH],
                                                     start[Position.HEIGHT])
            cells_in_path.add((current_width_pos, current_height_pos))
            for idx, letter in enumerate(path):
                if letter == "N":
                    current_height_pos -= 1
                elif letter == "E":
                    current_width_pos += 1
                elif letter == "S":
                    current_height_pos += 1
                elif letter == "W":
                    current_width_pos -= 1
                if (current_width_pos < 0
                        or current_width_pos >= max_width
                        or current_height_pos < 0
                        or current_height_pos >= max_height):
                    raise ValueError(f"Invalid path for {path[:idx+1]}"
                                     f" at position w: {current_width_pos}"
                                     f" h: {current_height_pos}"
                                     f' with start: ({start[Position.WIDTH]}'
                                     f', {start[Position.HEIGHT]})')
                cells_in_path.add((current_width_pos, current_height_pos))
            if (end[Position.WIDTH] != current_width_pos
                    or end[Position.HEIGHT] != current_height_pos):
                raise ValueError(f"Invalid path for {path}"
                                 f" end at w: {current_width_pos}"
                                 f" h: {current_height_pos} instead of "
                                 f" ({end[Position.WIDTH]},"
                                 f" {end[Position.HEIGHT]})")
            return cells_in_path

        try:
            maze_split = maze.split("\n")
            if maze_split and not maze_split[-1]:
                maze_split.pop(-1)
            width, height = extract_width_height(maze_split)
            cells = extract_cells(maze_split)
            check_newline(maze_split)
            start, end = extract_positions(maze_split, width, height)
            path = extract_path(maze_split, start, end, width, height)
            return MazeData(width, height, cells, start, end, path)
        except Exception as exception:
            raise ValueError("Invalid maze string: ", exception)
