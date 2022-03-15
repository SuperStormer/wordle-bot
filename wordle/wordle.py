from dataclasses import dataclass, field
from enum import Enum, auto
import string

@dataclass
class Wordle:
	actual: str
	guesses: list[str] = field(default_factory=list)
	remaining: list[str] = field(default_factory=lambda: list(string.ascii_lowercase))

class Square(Enum):
	WRONG = auto()
	PARTIAL = auto()
	FULL = auto()
