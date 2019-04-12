"""
.. _mailer:

mail module for exchange monitoring borg bots

:module:    mail_borg.mailer

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    apr. 10, 2019

"""
import collections

from uuid import uuid4
from exchangelib import ServiceAccount, Message, Account


def get_accounts(domain, user, password, email_addresses):
    """

    """
    credentials = ServiceAccount(
        username='{}\\{}'.format(domain, user), password=password)
    return [
        Account(primary_smtp_address=address,
                credentials=credentials,
                autodiscover=True) for address in email_addresses
    ]


MonMessage = collections.namedtuple(
    'MonMessage', ['message_id', 'message_acc'])


class ExhangeMonMessages():
    def __init__(self, accounts, email_addresses):
        self.messages = []
        for account in accounts:
            message_body = uuid4()
            self.messages.append(
                MonMessage(
                    message_id=message_body,
                    message_acc=Message(account=account,
                                        subject='exchange monitoring message',
                                        body=message_body,
                                        to_recipients=email_addresses)
                )
            )

    def send(self):
        for message in self.messages:
            message.message_acc.send()

    def verify_receive(self):
        for message in self.messages:
            if message.message_acc.inbox.filter(body__icontains=str(message.message_id)).count() == len(self.messages):
                # log ok
                continue
