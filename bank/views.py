import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID
import pandas as pd
import plotly.express as px
import plotly
import plotly.graph_objects as go
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from account.account import Account
from database.database import ObjectNotFound
from database.database import Database
from transaction.transaction import Transaction

dbname: str = "bank"
host: str = "localhost"
connection_str = f"database={dbname} port=5432 user=postgres password=12345 host=localhost"
database = Database()


def accounts_list(request: HttpRequest) -> HttpResponse:
    accounts = database.get_accounts()
    return render(request, "accounts.html", context={"accounts": accounts})


def transactions_list(request: HttpRequest, account_id) -> HttpResponse:
    transactions = database.get_transactions(account_id)
    account = database.get_account(account_id)
    list_accounts = database.get_accounts()
    return render(request, "transactions.html", context={"transactions": transactions, "account": account, "account_id": str(account_id), "list_accounts": list_accounts})

def accounts(request: HttpRequest) -> HttpResponse:
    accounts = database.get_accounts()

    if request.method == "GET":
        json_obj = [account.to_json() for account in accounts]
        return HttpResponse(content=json.dumps(json_obj))

    if request.method == "POST":
        try:
            account = Account(
                id_=None,
                currency=str(request.POST['currency']),
                balance=Decimal(0),
                is_max=0,
                date=str(datetime.now())
            )
            try:
                database.get_account(account.id_)
                return HttpResponse(content=f"Error: object already exists, use PUT to update", status=400)
            except ObjectNotFound:
                database.save_account(account)
                messages.success(request, f'Новый аккауунт с ID {str(account.id_)} создан успешно!\n Начальный баланс: 0 {account.currency}')
                return redirect('/accounts/')
        except Exception as e:
            return HttpResponse(content=f"Error: {e}", status=400)


def transactions(request: HttpRequest, account_id) -> HttpResponse:
    transactions = database.get_transactions(account_id)

    if request.method == "GET":
        json_obj = [transaction.to_json() for transaction in transactions]
        return HttpResponse(content=json.dumps(json_obj))

    if request.method == "POST":
        if request.POST["receiver"] == str(account_id):
            try:
                account = database.get_account(account_id)
            except:
                messages.error(request, 'Неверный ID аккаунта')
                return redirect('/' + str(account_id) + '/transactions/')

            if request.POST["amount"] == '':
                messages.error(request, 'Введите ненулевое значение для пополнения')
                return redirect('/' + str(account_id) + '/transactions/')

            try:
                account.balance += Decimal(request.POST["amount"])
                database.save_account(account)
            except:
                messages.error(request, 'Введите численное значение')
                return redirect('/' + str(account_id) + '/transactions/')

            transaction = Transaction(
                id_=uuid4(),
                sender=account.id_,
                receiver=account.id_,
                amount=Decimal(request.POST["amount"]),
                date=str(datetime.now()),
                status=True
            )
            database.save_transaction(transaction)
            messages.success(request, f"Аккаунт успешно пополнен! Текущий баланс: {str(account.balance)} {account.currency}")
            return redirect('/' + str(account_id) + '/transactions/')
        else:
            try:
                account_sender = database.get_account(request.POST["sender"])
            except:
                messages.error(request, 'Неверный ID отправителя')
                return redirect('/' + str(account_id) + '/transactions/')

            try:
                account_receiver = database.get_account(request.POST["receiver"])
            except:
                messages.error(request, 'Неверный ID получателя')
                return redirect('/' + str(account_id) + '/transactions/')


            if request.POST["amount"] == '':
                messages.error(request, 'Введите ненулевое значение для перевода')
                return redirect('/' + str(account_id) + '/transactions/')
            try:
                amount = Decimal(request.POST["amount"])
                if account_sender.balance >= amount:
                    transaction = Transaction(
                        id_=uuid4(),
                        sender=UUID(request.POST["sender"]),
                        receiver=UUID(request.POST["receiver"]),
                        amount=Decimal(request.POST["amount"]),
                        date=str(datetime.now()),
                        status=True
                    )
                    print(transaction)
                    try:
                        database.get_transaction(transaction.id_)
                        return HttpResponse(content=f"Error: object already exists, use PUT to update", status=400)
                    except ObjectNotFound:
                        database.save_transaction(transaction)
                        account_sender.balance -= amount
                        account_receiver.balance += amount
                        database.save_account(account_sender)
                        database.save_account(account_receiver)
                        messages.success(request, f"Успешний перевод между аккаунтами! Текущий баланс отправителя: {str(account_sender.balance)} {account_receiver.currency}, баланс получателя: {(account_receiver.balance)} {account_receiver.currency}")
                        return redirect('/' + str(account_id) + '/transactions/')
                else:
                    messages.error(request, 'Недостаточно средств для перевода')
                    return redirect('/'+str(account_id) + '/transactions/')
            except:
                messages.error(request, 'Введите численное значение')
                return redirect('/' + str(account_id) + '/transactions/')


def balance_history(request: HttpRequest, account_id) -> HttpResponse:
    transactions = database.get_transactions(account_id)
    transactions.reverse()
    balance = []
    date = []
    cur_balance = database.get_account(account_id).balance
    balance.append(cur_balance)

    for transaction in transactions:
        if transaction.receiver == account_id:
            cur_balance -= transaction.amount
        else:
            cur_balance += transaction.amount
        balance.append(cur_balance)
        date.append(transaction.date)
    date.append(database.get_account(account_id).date)
    balance.reverse()
    date.reverse()
    plot(balance, date, database.get_account(account_id).currency, account_id)
    return redirect('/accounts/')

def plot(balance, date, currency, account_id):
    df = pd.DataFrame(dict(
        x = date,
        y = balance
    ))

    fig = px.line(df, x="x", y=f"y", title=f"История изменения баланса аккаунта {account_id}", markers=True, text=balance, labels={'x': 'Дата', 'y': f'Баланс в {currency}'})
    fig.update_traces(textposition="bottom left")
    plotly.offline.plot(fig,filename='positives.html')