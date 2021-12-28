import sqlite3
from typing import List, Optional
from uuid import UUID, uuid4
import pandas as pd
from pandas import Series
from account.account import Account
from transaction.transaction import Transaction

class ObjectNotFound(ValueError):
    ...


class Database:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conn = sqlite3.connect('bank.db', check_same_thread = False)
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id varchar,
            currency varchar,
            balance decimal,
            is_max integer,
            creation_date date NULL,
            primary key(id)
        );
        """)
        cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id varchar,
                    sender varchar,
                    receiver varchar,
                    amount decimal,
                    transaction_date date NULL, 
                    status boolean NULL,
                    primary key (id),
                    foreign key (sender) references accounts (id),
                    foreign key (receiver) references accounts (id)
                );
                """)
        self.conn.commit()

    def close_connection(self):
        self.conn.close()

    def save_account(self, account: Account) -> None:
        cur = self.conn.cursor()
        cur.execute("""
                        UPDATE accounts SET is_max = 0 """)

        if account.id_ is None:
            account.id_ = uuid4()
            cur.execute("""
                            INSERT INTO accounts (id, currency, balance, is_max, creation_date) VALUES (?, ?, ?, 0, ?)
                            """, (str(account.id_), account.currency, account.balance, account.date))
        else:
            cur.execute("""
                            UPDATE accounts SET balance = ? where id = ?
                                        """, (account.balance, str(account.id_)))
        cur.execute("""
            UPDATE accounts SET is_max = 1 WHERE id in (select id from accounts group by currency having max(balance))
        """)
        self.conn.commit()

    def save_transaction(self, transaction: Transaction) -> None:
        transaction.id_ = uuid4()
        cur = self.conn.cursor()
        cur.execute("""
                INSERT INTO transactions (id, sender, receiver, amount, transaction_date, status) VALUES (?, ?, ?, ?, ?, ?)
                """, (str(transaction.id_), str(transaction.sender), str(transaction.receiver), transaction.amount, transaction.date, transaction.status))
        self.conn.commit()

    def get_accounts(self) -> List[Account]:
        self.con = sqlite3.connect('bank.db')
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM accounts")
        data = cur.fetchall()
        cols = [x[0] for x in cur.description]
        df = pd.DataFrame(data, columns=cols)
        return [self.pandas_row_to_account(row) for index, row in df.iterrows()]

    def get_transactions(self, account_id: UUID) -> List[Transaction]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE sender = ? or receiver = ?", (str(account_id), str(account_id)))
        data = cur.fetchall()
        cols = [x[0] for x in cur.description]
        df = pd.DataFrame(data, columns=cols)
        return [self.pandas_row_to_transaction(row) for index, row in df.iterrows()]

    def pandas_row_to_account(self, row: Series) -> Account:
        return Account(
            id_=UUID(row["id"]),
            currency=row["currency"],
            balance=row["balance"],
            is_max=row["is_max"],
            date=str(row["creation_date"]),
        )

    def pandas_row_to_transaction(self, row: Series) -> Transaction:
        return Transaction(
            id_=UUID(row["id"]),
            sender=UUID(row["sender"]),
            receiver=UUID(row["receiver"]),
            amount=row["amount"],
            date=str(row["transaction_date"]),
            status=row["status"]
        )

    def get_account(self, id_: UUID) -> Optional[Account]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE id = ?", (str(id_),))
        data = cur.fetchall()
        if len(data) == 0:
            raise ObjectNotFound("SQLite: Object not found")
        cols = [x[0] for x in cur.description]

        df = pd.DataFrame(data, columns=cols)
        return self.pandas_row_to_account(row=df.iloc[0])

    def get_transaction(self, id_: UUID) -> Optional[Transaction]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE id = ?", (str(id_),))
        data = cur.fetchall()
        if len(data) == 0:
            raise ObjectNotFound("SQLite: Object not found")
        cols = [x[0] for x in cur.description]

        df = pd.DataFrame(data, columns=cols)
        return self.pandas_row_to_transaction(row=df.iloc[0])
