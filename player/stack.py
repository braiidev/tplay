from __future__ import annotations
from typing import Literal
from dataclasses import dataclass, field
import random


@dataclass
class StackItem:
    path: str
    name: str
    mode: Literal["normal", "repeat_once", "repeat_inf"] = "normal"


class Stack:
    def __init__(self):
        self._items: list[StackItem] = []
        self.playhead: int = -1
        self.shuffle: bool = False
        self.repeat: bool = False

    @property
    def items(self) -> list[StackItem]:
        return self._items

    @items.setter
    def items(self, val: list[StackItem]):
        self._items = list(val)
        self.playhead = 0 if self._items else -1

    @property
    def current(self) -> StackItem | None:
        if 0 <= self.playhead < len(self._items):
            return self._items[self.playhead]
        return None

    @property
    def is_empty(self) -> bool:
        return not self._items

    @property
    def is_playing(self) -> bool:
        return self.playhead >= 0 and bool(self._items)

    def load_items(self, items: list[StackItem]) -> None:
        self._items = list(items)
        self.playhead = 0 if self._items else -1

    def append(self, item: StackItem) -> None:
        was_empty = not self._items
        self._items.append(item)
        if was_empty:
            self.playhead = 0

    def insert_after_current(self, item: StackItem) -> None:
        pos = self.playhead + 1 if self.playhead >= 0 else len(self._items)
        self._items.insert(pos, item)
        if self.playhead < 0:
            self.playhead = 0

    def remove(self, index: int) -> None:
        if index < 0 or index >= len(self._items):
            return
        self._items.pop(index)
        if self.playhead > index:
            self.playhead -= 1
        elif self.playhead == index:
            if self._items:
                self.playhead = min(self.playhead, len(self._items) - 1)
            else:
                self.playhead = -1

    def clear(self) -> None:
        self._items.clear()
        self.playhead = -1

    def swap(self, i: int, j: int) -> None:
        if not (0 <= i < len(self._items) and 0 <= j < len(self._items)):
            return
        self._items[i], self._items[j] = self._items[j], self._items[i]
        if self.playhead == i:
            self.playhead = j
        elif self.playhead == j:
            self.playhead = i

    def next_playhead(self) -> int:
        if not self._items:
            return -1
        if self.shuffle:
            candidates = [i for i in range(len(self._items)) if i != self.playhead]
            if candidates:
                return random.choice(candidates)
            return self.playhead if self.repeat else -1
        nxt = self.playhead + 1
        if nxt >= len(self._items):
            if self.repeat:
                return 0
            return -1
        return nxt

    def prev_playhead(self) -> int:
        if not self._items:
            return -1
        prev = self.playhead - 1
        if prev < 0:
            if self.repeat:
                return len(self._items) - 1
            return -1
        return prev

    def cycle_item_mode(self, index: int) -> None:
        if index < 0 or index >= len(self._items):
            return
        item = self._items[index]
        if item.mode == "normal":
            item.mode = "repeat_once"
        elif item.mode == "repeat_once":
            item.mode = "repeat_inf"
        else:
            item.mode = "normal"
