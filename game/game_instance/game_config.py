"""Configuration for the game."""


import json
from typing import Any, List, Optional, Tuple
from pydantic import (BaseModel, Field, field_validator)
from game.levelgen import LevelOptions
from Engine import Log


class GameConfig:
    """Config from the json.

    Attributes:
        highscore_filename: file storing the scores.
        lives: player lives.
        pacgum: pacgums in level.
        points_per_pacgum: points per pacgum eaten.
        points_per_super_pacgum: points per super pacgum eaten.
        points_per_ghost: points per ghost eaten.
        seed: seed for the first maze.
        levels_options: list of level options.
        level_max_time: max time for a level.
    """
    def __init__(self,
                 highscore_filename: str,
                 lives: int,
                 pacgum: int,
                 points_per_pacgum: int,
                 points_per_super_pacgum: int,
                 points_per_ghost: int,
                 seed: int,
                 levels_options: List[LevelOptions],
                 level_max_time: int) -> None:
        """Initilize the game configuration.

        Args:
            highscore_filename: file storing the scores.
            lives: player lives.
            pacgum: pacgums in level.
            points_per_pacgum: points per pacgum eaten.
            points_per_super_pacgum: points per super pacgum eaten.
            points_per_ghost: points per ghost eaten.
            seed: seed for the first maze.
            levels_options: list of level options.
            level_max_time: max time for a level.
        """
        self._highscore_filename = highscore_filename
        self._lives = lives
        self._pacgum = pacgum
        self._level_max_time = level_max_time
        self._points_per_pacgum = points_per_pacgum
        self._points_per_super_pacgum = points_per_super_pacgum
        self._points_per_ghost = points_per_ghost
        self._seed = seed
        self._levels_options = levels_options

    @property
    def points_per_pacgum(self) -> int:
        """Points per pacgum eaten."""
        return self._points_per_pacgum

    @property
    def points_per_super_pacgum(self) -> int:
        """Points per super pacgum eaten."""
        return self._points_per_super_pacgum

    @property
    def highscore_filename(self) -> str:
        """scores saves filename"""
        return self._highscore_filename

    @property
    def points_per_ghost(self) -> int:
        """Points per ghost eaten."""
        return self._points_per_ghost

    @property
    def lives(self) -> int:
        """Lives for the game."""
        return self._lives

    @property
    def level_max_time(self) -> int:
        """Maximum time for a level."""
        return self._level_max_time

    @property
    def seed(self) -> int:
        """The seed for the first maze."""
        return self._seed

    @property
    def levels_options(self) -> List[LevelOptions]:
        """Options for each level from the config."""
        return self._levels_options

    def __str__(self) -> str:
        """Returns a string representation.

        Returns:
            Returns a string representation.
        """
        levels_options_str = "\n  ".join([
            str(level_options)
            for level_options in self._levels_options
        ])
        return (
            f"GameConfig: \n"
            f"  highscore_filename={self._highscore_filename}\n"
            f"  lives={self._lives}\n"
            f"  pacgum={self._pacgum}\n"
            f"  level_max_time={self._level_max_time}\n"
            f"  points_per_pacgum={self._points_per_pacgum}\n"
            f"  points_per_super_pacgum={self._points_per_super_pacgum}\n"
            f"  points_per_ghost={self._points_per_ghost}\n"
            f"  seed={self._seed}\n"
            f"  {levels_options_str}"
        )


class GameConfigModelConstant:
    """Constants for the game config."""
    WIDTH = "width"
    HEIGHT = "height"
    DEFAULT_highscore_filename = "save_scores.json"
    MIN_width = 5
    MIN_height = 5
    MIN_lives = 1
    MIN_pacgum = 1
    MIN_points = 1
    DEFAULT_seed = 42
    MIN_level_max_time = 30  # seconds per level
    MIN_LEVELS = 10

    LOG = Log.get("main")


class GameConfigModel(BaseModel):  # type: ignore[misc]
    """Model for game config validation for the config file."""

    highscore_filename: str = Field(default="save_scores.json")
    level: List[Tuple[int, int]] = Field(default=[(15, 15), (15, 15), (15, 15),
                                                  (15, 15), (15, 15), (15, 15),
                                                  (15, 15), (15, 15), (15, 15),
                                                  (15, 15)])
    lives: int = Field(gt=0, default=3)
    pacgum: int = Field(default=42)
    points_per_pacgum: int = Field(default=10)
    points_per_super_pacgum: int = Field(default=50)
    points_per_ghost: int = Field(default=200)
    seed: int = Field(default=42)
    level_max_time: int = Field(default=90)

    @staticmethod
    def check_number(v: Any,
                     min_value: int,
                     name: str
                     ) -> int:
        """Returns the correct int v or min_value.

        Try returning v as int and upper than min_value, else min_value.

        Returns:
            Returns v if valid or min_value.
        """
        try:
            number = int(v)
            if number >= min_value:
                return number
            GameConfigModelConstant.LOG.error(
                f"{name} too low: {number}."
                f" Use {min_value}.")
            return min_value
        except Exception:
            GameConfigModelConstant.LOG.error(
                f"{name} invalid: {v}."
                f" Use {min_value}.")
            return min_value

    @field_validator("highscore_filename", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_highscore_filename(cls, v: Any) -> str:
        """Returns the string for the filename, or default.

        Returns:
            Returns the string for the filename, or default if error.
        """
        try:
            return str(v)  # TODO: check if can open file ?
        except Exception:
            GameConfigModelConstant.LOG.error(
                f"Invalid score filename: {v}."
                f" Use {GameConfigModelConstant.DEFAULT_highscore_filename}.")
            return GameConfigModelConstant.DEFAULT_highscore_filename

    @field_validator("lives", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_lives(cls, v: Any) -> int:
        """Returns the correct int v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        return GameConfigModel.check_number(
            v,
            GameConfigModelConstant.MIN_lives,
            "lives")

    @field_validator("pacgum", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_pacgum(cls, v: Any) -> int:
        """Returns the correct int v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        return GameConfigModel.check_number(
            v,
            GameConfigModelConstant.MIN_pacgum,
            "pacgum")

    @field_validator("seed", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_seed(cls, v: Any) -> int:
        """Returns the correct int v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        try:
            return int(v)
        except Exception:
            GameConfigModelConstant.LOG.error(
                f"Seed invalid: {v}."
                f" Use {GameConfigModelConstant.DEFAULT_seed}.")
            return GameConfigModelConstant.DEFAULT_seed

    @field_validator("points_per_pacgum", "points_per_super_pacgum",
                     "points_per_ghost", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_points(cls, v: Any) -> int:
        """Returns the correct int v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        return GameConfigModel.check_number(
            v,
            GameConfigModelConstant.MIN_points,
            "points")

    @field_validator("level_max_time", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_level_max_time(cls, v: Any) -> int:
        """Returns the correct int v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        return GameConfigModel.check_number(
            v,
            GameConfigModelConstant.MIN_level_max_time,
            "level_max_time")

    @staticmethod
    def _validate_level_entry(
        level_data: Any
    ) -> Optional[Tuple[int, int]]:
        """Validate a single level entry and return (width, height)."""
        if not isinstance(level_data, dict):
            GameConfigModelConstant.LOG.error(
                f"Not a dict: {level_data}. Ignored.")
            return None

        if (GameConfigModelConstant.WIDTH not in level_data
                or GameConfigModelConstant.HEIGHT not in level_data):
            GameConfigModelConstant.LOG.error(
                f"Level without keys {GameConfigModelConstant.WIDTH} or "
                f"{GameConfigModelConstant.HEIGHT}. Ignored.")
            return None

        try:
            width = int(level_data[GameConfigModelConstant.WIDTH])
            height = int(level_data[GameConfigModelConstant.HEIGHT])
        except Exception:
            GameConfigModelConstant.LOG.error(
                f"Invalid width={level_data[GameConfigModelConstant.WIDTH]}, "
                f"height={level_data[GameConfigModelConstant.HEIGHT]}. "
                "Ignored.")
            return None

        if width < GameConfigModelConstant.MIN_width:
            GameConfigModelConstant.LOG.error(
                f"Width too small: {width}. Use "
                f"{GameConfigModelConstant.MIN_width}.")
            width = GameConfigModelConstant.MIN_width

        if height < GameConfigModelConstant.MIN_height:
            GameConfigModelConstant.LOG.error(
                f"Height too small: {height}. Use "
                f"{GameConfigModelConstant.MIN_height}.")
            height = GameConfigModelConstant.MIN_height

        return (width, height)

    @field_validator("level", mode="before")  # type: ignore[misc]
    @classmethod
    def parse_level(cls, v: Any) -> List[Tuple[int, int]]:
        """Returns the correct List[Tuple[int, int]] v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        if not isinstance(v, list):
            GameConfigModelConstant.LOG.error(
                f"Not a list: {v}. Ignored.")
            raise ValueError("Bad Json, use default.")

        levels_options: List[Tuple[int, int]] = []
        for level_data in v:
            result = GameConfigModel._validate_level_entry(level_data)
            if result is not None:
                levels_options.append(result)

        if not levels_options:
            GameConfigModelConstant.LOG.error(
                "No valid level options found. Use default.")
            raise ValueError("No valid levels, use default.")

        return levels_options


class GameConfigParser:
    """Game config parser."""
    @staticmethod
    def parse(config_filename: str) -> GameConfig:
        """Returns the GameConfig from the file, or default.

        Args:
            config_filename: the filename for the game config.

        Returns:
            Returns the GameConfig from the file, or default.
        """
        try:
            with open(config_filename) as f:
                json_data = json.load(f)
        except Exception:
            GameConfigModelConstant.LOG.error(
                "Invalid game config json file. Use default.")
            return GameConfigParser.default_game_config()

        try:
            gcm = GameConfigModel.model_validate(json_data)

            levels_options_tuple = gcm.level
            levels_options = [
                LevelOptions(width,
                             height,
                             gcm.pacgum,
                             None,
                             gcm.level_max_time)  # Default
                for width, height in levels_options_tuple
            ]
            if len(levels_options) < GameConfigModelConstant.MIN_LEVELS:
                GameConfigModelConstant.LOG.error(
                    f"No enough levels: {len(levels_options)}. Add default to "
                    f"{GameConfigModelConstant.MIN_LEVELS} levels.")
                levels_options.extend(
                    GameConfigParser.default_levels_options(
                    )[:max(0, GameConfigModelConstant.MIN_LEVELS
                           - len(levels_options))])

            for level_options in levels_options:
                level_options.pac_gum_count = gcm.pacgum
                level_options.seed = None
            if levels_options:
                levels_options[0].seed = gcm.seed

            return GameConfig(
                points_per_pacgum=gcm.points_per_pacgum,
                points_per_super_pacgum=gcm.points_per_super_pacgum,
                points_per_ghost=gcm.points_per_ghost,
                seed=gcm.seed,
                levels_options=levels_options,
                highscore_filename=gcm.highscore_filename,
                lives=gcm.lives,
                pacgum=gcm.pacgum,
                level_max_time=gcm.level_max_time
            )
        except Exception as e:
            GameConfigModelConstant.LOG.error(
                f"Invalid game config parse model. Use default. {e}")
            return GameConfigParser.default_game_config()

    @staticmethod
    def default_game_config() -> GameConfig:
        """Returns the default GameConfig.

        Returns:
            Returns the default GameConfig.
        """
        levels_options = GameConfigParser.default_levels_options()
        seed = 42
        levels_options[0].seed = seed
        return GameConfig(
            points_per_pacgum=5,
            points_per_super_pacgum=10,
            points_per_ghost=200,
            seed=seed,
            levels_options=levels_options,
            highscore_filename=(
                GameConfigModelConstant.DEFAULT_highscore_filename),
            lives=3,
            pacgum=42,
            level_max_time=90
        )

    @staticmethod
    def default_levels_options() -> List[LevelOptions]:
        """Returns the default list of LevelOptions.

        Returns:
            Returns the default list of LevelOptions.
        """
        return [
            LevelOptions(15, 15, 42, seed=None),
            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),

            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),
            LevelOptions(15, 15, 42),
        ]
