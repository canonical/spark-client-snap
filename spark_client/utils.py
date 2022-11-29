"""Module for general logging functionalities and abstractions."""

import errno
import io
import os
import subprocess
from copy import deepcopy as copy
from functools import reduce
from logging import getLogger, Logger
from tempfile import NamedTemporaryFile
from typing import Callable, Union, Any, Literal, TypedDict, Mapping, Dict
import yaml

PathLike = Union[str, "os.PathLike[str]"]

LevelTypes = Literal[
    "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET", 50, 40, 30, 20, 10, 0
]
StrLevelTypes = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]


class LevelsDict(TypedDict):
    CRITICAL: Literal[50]
    ERROR: Literal[40]
    WARNING: Literal[30]
    INFO: Literal[20]
    DEBUG: Literal[10]
    NOTSET: Literal[0]


DEFAULT_LOG_LEVEL: StrLevelTypes = "INFO"

levels: LevelsDict = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}


class WithLogging:
    """Base class to be used for providing a logger embedded in the class."""

    @property
    def logger(self) -> Logger:
        """
        Create logger.
        :return: default logger
        """
        nameLogger = str(self.__class__).replace("<class '", "").replace("'>", "")
        return getLogger(nameLogger)

    def logResult(
            self, msg: Union[Callable[..., str], str], level: StrLevelTypes = "INFO"
    ) -> Callable[..., Any]:
        """
        Return a decorator to allow logging of inputs/outputs.
        :param msg: message to log
        :param level: logging level
        :return: wrapped method
        """

        def wrap(x: Any) -> Any:
            if isinstance(msg, str):
                self.logger.log(levels[level], msg)
            else:
                self.logger.log(levels[level], msg(x))
            return x

        return wrap


def union(*dicts: dict) -> dict:
    """
    Return a dictionary that results from the recursive merge of the input dictionaries.
    :param dicts: list of dicts
    :return: merged dict
    """

    def __dict_merge(dct: dict, merge_dct: dict):
        """
        Recursive dict merge.
        Inspired by :meth:``dict.update()``, instead of updating only top-level keys, dict_merge recurses down into
        dicts nested to an arbitrary depth, updating keys. The ``merge_dct`` is merged into ``dct``.
        :param dct: dict onto which the merge is executed
        :param merge_dct: dct merged into dct
        :return: None
        """
        merged = copy(dct)
        for k, v in merge_dct.items():
            if (
                    k in dct
                    and isinstance(dct[k], dict)
                    and isinstance(merge_dct[k], Mapping)
            ):
                merged[k] = __dict_merge(dct[k], merge_dct[k])
            else:
                merged[k] = merge_dct[k]
        return merged

    return reduce(__dict_merge, dicts)


def umask_named_temporary_file(*args, **kargs):
    """Return a temporary file descriptor readable by all users."""
    file_desc = NamedTemporaryFile(*args, **kargs)
    mask = os.umask(0o666)
    os.umask(mask)
    os.chmod(file_desc.name, 0o666 & ~mask)
    return file_desc


def mkdir(path: PathLike) -> None:
    """
    Create a dir, using a formulation consistent between 2.x and 3.x python versions.
    :param path: path to create
    :raises OSError: whenever OSError is raised by makedirs and it's not because the directory exists
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def create_dir_if_not_exists(directory: PathLike) -> PathLike:
    """
    Create a directory if it does not exist.
    :param directory: path
    :return: directory, str
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def parse_yaml_shell_output(cmd: str) -> Union[Dict[str, Any], str]:
    with io.StringIO() as buffer:
        buffer.write(subprocess.check_output(cmd, shell=True, stderr=None).decode("utf-8"))
        buffer.seek(0)
        return yaml.safe_load(buffer)
