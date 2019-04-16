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

from config import get_config
from logger import LogWinEvent


def get_accounts(domain=None, username=None, password=None,
                 email_addresses=None, logger=None):
    """
    get a list of Exchange accounts

    the assumption is that the same domain account has multiple
    Exchange accounts and that we want to verify all these accounts

    :arg str domain: the windows domain

    :arg str username: the domain user name

    :arg str password: the password

    :arg list email_addresses:

        the list SMTP aliases,  i.e. the Exchange accounts for this
        particular user

    :arg logger: windows events log writer
    :argtype logger: :class:`<logger.WinLogEvent>`

    """
    if domain is None:
        domain = get_config().get('domain')

    if username is None:
        username = get_config().get('username')

    if password is None:
        password = get_config().get('password')

    if email_addresses is None:
        email_addresses = get_config().get('email_addresses')

    if not isinstance(email_addresses, (list, tuple)):
        email_addresses = [email_addresses]

    if logger is None:
        logger = LogWinEvent()

    credentials = ServiceAccount(
        username='{}\\{}'.format(domain, username), password=password)

    accounts = []
    for address in email_addresses:
        try:
            accounts.append(Account(primary_smtp_address=address,
                                    credentials=credentials,
                                    autodiscover=True))
            logger.info(
                strings=[
                    'message: "connected to the exchange server"',
                    'account: %s\\%s, %s' % (domain, username, address), ])
        except Exception as err:  # pylint: disable=broad-except
            logger.err(
                strings=[
                    'message: "cannot connect to the exchange server"',
                    'account: %s\\%s, %s' % (domain, username, address),
                    'exception: %s' % str(err), ])

    return accounts


WitnessMessage = collections.namedtuple(
    'WitnessMessage', ['message_uuid', 'account_for_message'])
"""
:var WitnessMessage: name tuple class describing an exchange message

    *    :message_uuid: an unique identifier for the message
                        used for retrieving the message from the inbox
                        so as to verify that it was received

    *    :account_for_message: the exchange account used to send the
                               message

:vartype WitnessMessage: :class:`<collections.namedtuple>`
"""


class WitnessMessages():
    """
    class for sent and received messages

    a message is an ``uuid`` instance generated via : method:`<uuid.uuid4>`.
    this way each message is its own unique identifier and can be searched
    for in the inbox

    an exchange account is defined by the domain account and by all the
    SMPT aliases associated with the account. for example:

    *    PHSABC\\serban.teodorescu with serban.teodorescu@phsa.ca is an account

    *    PHSABC\\serban.teodorescu with serban.teodorescu@hssbc.org is
         another account

    a monitoring or witness message is a message that has been successfully
    sent from one account to itself and all the other accounts and then has
    been identified in the inbox of each account. for example:
    the message wih UUID: xxxxx will be sent from serban.teodorescu@phsa.ca
    to serban.teodorescu@phsa.ca and serban.teodorescu@hssbc.org. if the
    send operation executed with no errors and we can retrieve the message
    from the inbox of both serban.teodorescu@phsa.ca and
    serban.teodorescu@hssbc.org within a reasonable amount of time, we
    are assuming that exchange functionality has been proven for the
    account that was used to send this message (in this case,
    serban.teodorescu@phsa.ca)

    """

    def __init__(self, accounts=None, email_addresses=None, logger=None):
        """
        constructor

        :arg list accounts: a list of :class:`<exchangelib.Account>` objects

        :arg list email_addresses:

            the list SMTP aliases,  i.e. the Exchange accounts for this
            particular user

        :arg logger: windows events log writer
        :argtype logger: :class:`<logger.WinLogEvent>`
        """
        self.messages = []
        for account in accounts:
            message_body = uuid4()
            self.messages.append(
                WitnessMessage(
                    message_uuid=message_body,
                    account_for_message=Message(account=account,
                                                subject='exchange monitoring message',
                                                body=message_body,
                                                to_recipients=email_addresses)
                )
            )

    def send(self):
        for message in self.messages:
            message.account_for_message.send()

    def verify_receive(self):
        for message in self.messages:
            if message.account_for_message.inbox.filter(body__icontains=str(message.message_uuid)).count() == len(self.messages):
                # log ok
                continue
