"""One creature: body samples the head's world-space path by travelled distance."""

from bisect import bisect_right
from dataclasses import dataclass, field
from math import ceil, hypot
from typing import ClassVar

from .enemies import Enemy


@dataclass
class Segment:
    x: float
    y: float
    hp: float = 10
    max_hp: float = 10
    radius: float = 22


@dataclass
class Worm(Enemy):
    hp: float = 60
    max_hp: float = 60
    speed: float = 55
    damage: float = 18
    radius: float = 22
    kind: str = "worm"
    segments: list = field(default_factory=list)
    _trail: list = field(default_factory=list, init=False, repr=False)
    _head_distance: float = field(default=0.0, init=False, repr=False)
    _arena: tuple | None = field(default=None, init=False, repr=False)

    segment_spacing: ClassVar[float] = 32.0
    trail_step: ClassVar[float] = 2.0
    trail_margin: ClassVar[float] = 64.0
    trail_capacity: ClassVar[int] = 2048

    def __post_init__(self):
        if not self.segments:
            self.segments = [Segment(self.x - index * self.segment_spacing, self.y)
                             for index in range(6)]
        self.hp = sum(segment.hp for segment in self.segments)
        self.reset_trail()

    @property
    def head(self):
        return self.segments[0] if self.segments else None

    @property
    def head_hp(self):
        return self.head.hp if self.head else 0

    @property
    def trail_snapshot(self):
        """Immutable (arc distance, x, y) points, oldest to newest."""
        return tuple(self._trail)

    def _inside(self, x, y):
        if self._arena is None:
            return True
        left, top, width, height = self._arena
        return (left + self.radius - 1e-9 <= x <= left + width - self.radius + 1e-9
                and top + self.radius - 1e-9 <= y <= top + height - self.radius + 1e-9)

    def _clamp_head(self):
        if self._arena is not None:
            left, top, width, height = self._arena
            self.x = max(left + self.radius, min(left + width - self.radius, self.x))
            self.y = max(top + self.radius, min(top + height - self.radius, self.y))

    def _seed_inside_arena(self):
        """Only used at spawn: seed a deterministic path entirely inside walls."""
        left, top, width, height = self._arena
        minimum_x, maximum_x = left + self.radius, left + width - self.radius
        minimum_y, maximum_y = top + self.radius, top + height - self.radius
        choices = ((maximum_x - self.x, 1, 0), (self.x - minimum_x, -1, 0),
                   (maximum_y - self.y, 0, 1), (self.y - minimum_y, 0, -1))
        _, nx, ny = max(choices, key=lambda value: value[0])
        positions = [(self.x, self.y)]
        x, y = self.x, self.y
        # Tiny arenas can require the seeded path to double back on itself.
        for _ in self.segments[1:]:
            remaining = self.segment_spacing
            while remaining > 1e-9:
                available = (maximum_x - x if nx > 0 else x - minimum_x) if nx else (
                    maximum_y - y if ny > 0 else y - minimum_y)
                if available < 1e-9:
                    nx, ny = -nx, -ny
                    available = (maximum_x - minimum_x) if nx else (maximum_y - minimum_y)
                    if available < 1e-9:
                        remaining = 0
                        break
                step = min(remaining, available)
                x, y = x + nx * step, y + ny * step
                remaining -= step
                if step == available and remaining > 1e-9:
                    positions.append((x, y))
                    nx, ny = -nx, -ny
            positions.append((x, y))
        return positions

    def reset_trail(self, arena=None):
        """Explicit rebase after spawn placement, never on ordinary turns."""
        if arena is not None:
            self._arena = tuple(arena)
        self._trail.clear()
        self._head_distance = 0.0
        if not self.head:
            return
        self._clamp_head()
        self.head.x, self.head.y = self.x, self.y
        positions = [(part.x, part.y) for part in self.segments]
        if self._arena is not None and any(not self._inside(x, y) for x, y in positions):
            positions = self._seed_inside_arena()
        distance = 0.0
        reverse = [(0.0, *positions[0])]
        for x, y in positions[1:]:
            previous = reverse[-1]
            length = hypot(x - previous[1], y - previous[2])
            if length > 1e-9:
                distance += length
                reverse.append((-distance, x, y))
        self._trail = list(reversed(reverse))
        self._place_segments()

    def sample_trail(self, distance_behind):
        """Sample arc length; tight turns need not have 32px Euclidean spacing."""
        if not self._trail:
            return self.x, self.y
        target = self._head_distance - max(0.0, distance_behind)
        if target <= self._trail[0][0]:
            return self._trail[0][1:]
        if target >= self._trail[-1][0]:
            return self._trail[-1][1:]
        index = bisect_right(self._trail, (target, float("inf"), float("inf")))
        before, after = self._trail[index - 1], self._trail[index]
        ratio = (target - before[0]) / (after[0] - before[0])
        return (before[1] + (after[1] - before[1]) * ratio,
                before[2] + (after[2] - before[2]) * ratio)

    def _place_segments(self):
        for index, segment in enumerate(self.segments):
            segment.x, segment.y = self.sample_trail(index * self.segment_spacing)

    def _prune_trail(self):
        cutoff = self._head_distance - (len(self.segments) - 1) * self.segment_spacing - self.trail_margin
        index = max(0, bisect_right(self._trail, (cutoff, float("inf"), float("inf"))) - 1)
        if index:
            del self._trail[:index]
        # Bound memory even for microscopic simulation time steps.
        while len(self._trail) > self.trail_capacity:
            self._trail = self._trail[:1] + self._trail[1:-1:2] + self._trail[-1:]

    def receive_damage(self, amount) -> float:
        if not self.head:
            return 0
        previous = self.hp
        self.head.hp = max(0, self.head.hp - max(0, amount))
        if self.head.hp <= 0:
            self.segments.pop(0)  # Overkill never damages the following head.
            if self.head:
                target = self._head_distance - self.segment_spacing
                expected = self.sample_trail(self.segment_spacing)
                self.x, self.y = self.head.x, self.head.y
                if hypot(self.x - expected[0], self.y - expected[1]) > 1e-6:
                    # Also tolerate explicit repositioning by tools/test fixtures.
                    self.reset_trail()
                else:
                    index = bisect_right(self._trail, (target, float("inf"), float("inf")))
                    self._trail = self._trail[:index]
                    if not self._trail or self._trail[-1][0] < target - 1e-9:
                        self._trail.append((target, self.x, self.y))
                    self._head_distance = target
                    self._prune_trail()
            else:
                self._trail.clear()
        self.hp = sum(segment.hp for segment in self.segments)
        return previous - self.hp

    def translate_rigid(self, dx, dy):
        """External separation/pulse translates the whole creature and its path."""
        for segment in self.segments:
            segment.x += dx
            segment.y += dy
        self.x += dx
        self.y += dy
        self._trail = [(s, x + dx, y + dy) for s, x, y in self._trail]

    def translation_limits(self, arena):
        """Include the path between parts, so future samples also stay inside."""
        left, top, width, height = arena
        oldest = self._head_distance - (len(self.segments) - 1) * self.segment_spacing
        points = [(part.x, part.y) for part in self.segments]
        points.extend((x, y) for s, x, y in self._trail if s >= oldest)
        if not points:
            points = [(self.x, self.y)]
        return (max(left + self.radius - x for x, _ in points),
                min(left + width - self.radius - x for x, _ in points),
                max(top + self.radius - y for _, y in points),
                min(top + height - self.radius - y for _, y in points))

    def _follow_segments(self, arena=None) -> None:
        if not self.head:
            return
        if arena is not None:
            previous_arena = self._arena
            self._arena = tuple(arena)
            if previous_arena is None and any(not self._inside(part.x, part.y) for part in self.segments):
                self.reset_trail(arena)
        self._clamp_head()
        if not self._trail:
            self.reset_trail(arena)
        _, old_x, old_y = self._trail[-1]
        dx, dy = self.x - old_x, self.y - old_y
        distance = hypot(dx, dy)
        if distance > 1e-9:
            steps = max(1, ceil(distance / self.trail_step))
            origin = self._head_distance
            for index in range(1, steps + 1):
                fraction = index / steps
                self._trail.append((origin + distance * fraction,
                                    old_x + dx * fraction, old_y + dy * fraction))
            self._head_distance += distance
            self._prune_trail()
        self._place_segments()

    def advance_feedback(self, dt, arena) -> float:
        free_time = super().advance_feedback(dt, arena)
        self._follow_segments(arena)
        return free_time

    def move_towards(self, player, dt) -> None:
        super().move_towards(player, dt)
        self._follow_segments()
