from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID
import json


@dataclass
class Account:
    id_: Optional[UUID]
    currency: str
    balance: Decimal
    is_max: int
    date: str = None

    def to_json(self) -> dict:
        return {
            "id": str(self.id_),
            "currency": self.currency,
            "balance": float(self.balance),
            "is_max": int,
            "date": str(self.date),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json())

    @classmethod
    def from_json_str(cls, json_str: str) -> "Account":
        obj = json.loads(json_str)
        assert "currency" in obj
        assert "balance" in obj

        if "id" not in obj:
            raise ValueError("id should be in json string!")

        return cls(
            id_=UUID(obj["id"]),
            currency=obj["currency"],
            balance=Decimal(obj["balance"]),
            is_max=int(obj["is_max"]),
            date=obj["date"]
        )