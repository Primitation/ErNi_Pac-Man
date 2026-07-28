"""Configuration for the game."""


import json
from typing import Any, List, Tuple
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
                 highscore_filename,
                 lives,
                 pacgum,
                 points_per_pacgum,
                 points_per_super_pacgum,
                 points_per_ghost,
                 seed,
                 levels_options,
                 level_max_time) -> None:
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
    def highscore_filename(self) -> int:
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
    MIN_LEVELS = 1  # TODO REAL VALUE NEEDED: 10

    LOG = Log.get("main")


class GameConfigModel(BaseModel):
    """Model for game config validation for the config file."""

    highscore_filename: str = Field(default="save_scores.json")
    level: List[Tuple[int, int]]
    lives: int = Field(gt=0)
    pacgum: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int
    level_max_time: int

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

    @field_validator("highscore_filename", mode="before")
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

    @field_validator("lives", mode="before")
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

    @field_validator("pacgum", mode="before")
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

    @field_validator("seed", mode="before")
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
                     "points_per_ghost", mode="before")
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

    @field_validator("level_max_time", mode="before")
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

    @field_validator("level", mode="before")
    @classmethod
    def parse_level(cls, v: Any) -> List[Tuple[int, int]]:
        """Returns the correct List[Tuple[int, int]] v or default.

        Try returning v as int and upper than default, else default.

        Returns:
            Returns v if valid or default.
        """
        try:
            levels_options: List[Tuple[int, int]] = []
            levels_data = v
            if isinstance(levels_data, list):
                for level_data in levels_data:
                    if isinstance(level_data, dict):
                        if (GameConfigModelConstant.WIDTH in level_data
                                and GameConfigModelConstant.HEIGHT
                                in level_data):
                            width_base = (
                                level_data[GameConfigModelConstant.WIDTH]
                            )
                            height_base = (
                                level_data[GameConfigModelConstant.HEIGHT]
                            )
                            try:
                                width = int(width_base)
                                height = int(height_base)
                            except Exception:
                                GameConfigModelConstant.LOG.error(
                                    f"Invalid width={width_base},"
                                    f" height={height_base}. Ignored.")
                                continue
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

                            levels_options.append((width, height))
                        else:
                            GameConfigModelConstant.LOG.error(
                                f"Level without keys "
                                f"{GameConfigModelConstant.WIDTH} or "
                                f"{GameConfigModelConstant.HEIGHT}. Ignored.")
                            continue
                    else:
                        GameConfigModelConstant.LOG.error(
                            f"Not a dict: {level_data}. Ignored.")
                        continue
            else:
                GameConfigModelConstant.LOG.error(
                    f"Not a list: {levels_data}. Ignored.")
                raise ValueError("Bad Json, use default.")
            return levels_options

        except Exception:
            GameConfigModelConstant.LOG.error(
                    f"Invalids level options. Use default.")
            return []  # Default by GameConfigParser


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
                f"Invalid game config json file. Use default.")
            return GameConfigParser.default_game_config()

        try:
            gcm = GameConfigModel.model_validate(json_data)

            levels_options_tuple = gcm.level
            levels_options = [
                LevelOptions(width,
                             height,
                             gcm.pacgum,
                             None)  # Default
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
            LevelOptions(200, 100, 4, seed=None),
            LevelOptions(250, 50, 8),
            LevelOptions(100, 150, 6),
            LevelOptions(100, 100, 11),
            LevelOptions(50, 50, 11),
            LevelOptions(250, 50, 8),
            LevelOptions(100, 150, 6),
            LevelOptions(100, 100, 11),
            LevelOptions(50, 50, 11),
            LevelOptions(50, 50, 11),
        ]
