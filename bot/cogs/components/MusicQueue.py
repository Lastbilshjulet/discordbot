import random
from enum import Enum
from discord.ext import commands


class QueueIsEmpty(commands.CommandError):
    pass


class RepeatMode(Enum):
    NONE = 0
    SONG = 1
    QUEUE = 2


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if self.is_empty:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if self.is_empty:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if self.is_empty:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self.upcoming)

    @property
    def tracks_length(self):
        len = self.current_track.length
        for track in self.upcoming:
            len += track.length
        return len

    def add(self, *args):
        self._queue.extend(args)

    def get(self, index):
        return self._queue[index]

    def move(self, index, dest):
        track = self._queue.pop(index)
        self._queue.insert(dest, track)

    def remove(self, index):
        self._queue.pop(index)

    def get_next_track(self):
        if self.is_empty:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.QUEUE:
                self.position = 0
            else:
                return None

        return self._queue[self.position]

    def shuffle(self):
        if self.is_empty:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def update_repeat_mode(self):
        if self.repeat_mode == RepeatMode.NONE:
            self.repeat_mode = RepeatMode.SONG
        elif self.repeat_mode == RepeatMode.SONG:
            self.repeat_mode = RepeatMode.QUEUE
        elif self.repeat_mode == RepeatMode.QUEUE:
            self.repeat_mode = RepeatMode.NONE

    def empty(self):
        curr_track = self.current_track
        self._queue.clear()
        self.position = 0
        self._queue.append(curr_track)
