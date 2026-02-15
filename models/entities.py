from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Account:
    id: int | None
    name: str
    kind: str
    balance: float


@dataclass(slots=True)
class Transaction:
    id: int | None
    date: str
    description: str
    category: str
    account: str
    amount: float
    type: str


@dataclass(slots=True)
class Budget:
    id: int | None
    month: str
    category: str
    planned: float


@dataclass(slots=True)
class Goal:
    id: int | None
    name: str
    target: float
    current: float
    deadline: str | None
