import json
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

@dataclass
class Transaction:
    id_: UUID
    sender: UUID
    receiver: UUID
    amount: Decimal
    date: str = None
    status: bool = None

    def to_json(self) -> dict:
        return {
            "id": str(self.id_),
            "sender": str(self.sender),
            "receiver": str(self.receiver),
            "amount": float(self.amount),
            "date": str(self.date),
            "status": str(self.status),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json())

    @classmethod
    def from_json_str(cls, json_str: str) -> "Transaction":
        obj = json.loads(json_str)
        assert "currency" in obj
        assert "balance" in obj

        if "id" not in obj:
            raise ValueError("id should be in json string!")

        return cls(
            id_=UUID(obj["id"]),
            sender=UUID(obj["sender"]),
            receiver=UUID(obj["receiver"]),
            amount=Decimal(obj["amount"]),
            date=obj["date"],
            status=obj["status"],
        )
