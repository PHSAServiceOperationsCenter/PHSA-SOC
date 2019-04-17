"""
.. _mailer:

mail module for exchange monitoring borg bots

:module:    mail_borg.mailer

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    apr. 10, 2019

notes
=====

we will avoid the use of list comprehensions because of the way we want to
handle exceptions in this module.
in most cases, if there is a problem with a list item, we want to log the
problem and continue processing. that is not supported with list
comprehensions; if an exception occurs, processing will be stopped even if
we catch the error.

"""
import collections

from uuid import uuid4

from exchangelib import ServiceAccount, Message, Account
from email_validator import (
    validate_email, EmailSyntaxError, EmailUndeliverableError,
)
from timeout_decorator import timeout, TimeoutError

from config import get_config
from logger import LogWinEvent


@timeout(get_config().get('check_mx_timeout', 15))
def validate_email_to_ascii(  # pylint: disable=too-many-arguments
        email_address, to_ascii=True, allow_smtputf8=False,
        check_deliverability=True, logger=None):
    """
    validate, normalize, and return an email address
    optionally also convert it to ascii

    the timeout decorator is required because the current pypi version
    of the :module:`<email_validator>` doesn't implement a timeout when
    checking the MX record for an email address

    :arg bool to_ascii: default ``True``

        see below for SMTPUTF8 support. i am pretty sure that any recent
        Exchange version will support characters like è but this is
        British Columbia and they don't always play nice with the feds or
        with Québec

    :arg bool allow_smtputf8: default ``False``

        it is unclear whether Exchange supports SMTPUTF8 in versions 2016
        or lower so let's stay away from all that nonsense

    :arg bool check_deliverability: default True

        does the domain part of the email address resolve? this should be
        checked because it may show us DNS errors on some borg nodes

    :returns:

        a valid, normalized email address value or ``None`` if the
        validation fails. see the :raises: section for a discussion about this

    :raises:

        this function doesn't raise any exceptions because it does its own
        error handling by logging specific failures to the windows events log
    """
    if logger is None:
        logger = LogWinEvent()

    try:
        email_dict = validate_email(
            email_address, allow_smtputf8=allow_smtputf8,
            allow_empty_local=False, check_deliverability=check_deliverability)
    except (EmailSyntaxError, EmailUndeliverableError) as error:
        logger.err(strings=[
            'message: bad email address %s' % email_address,
            'exception: %s' % str(error)])
        return None

    if to_ascii:
        return email_dict.get('email_ascii')

    return email_dict.get('email')


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
    if logger is None:
        logger = LogWinEvent()

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

    emails = []
    for email_address in email_addresses:
        emails.append(validate_email_to_ascii(email_address, logger=logger))

    if not emails:
        logger.error(strings=[
            'message: none of the %s email addresses are valid.'
            'please update your configuration for this node',
            'invalid or unknown email addresses: %s'
            % ', '.join(email_addresses), ])
        return None

    credentials = ServiceAccount(
        username='{}\\{}'.format(domain, username), password=password)

    accounts = []
    for email in emails:
        try:
            accounts.append(Account(primary_smtp_address=email,
                                    credentials=credentials,
                                    autodiscover=True))
            logger.info(
                strings=[
                    'message: "connected to the exchange server"',
                    'account: %s\\%s, %s' % (domain, username, email), ])
        except Exception as err:  # pylint: disable=broad-except
            logger.err(
                strings=[
                    'message: "cannot connect to the exchange server"',
                    'account: %s\\%s, %s' % (domain, username, email),
                    'exception: %s' % str(err), ])

    if not accounts:
        logger.error(strings=[
            'message: no valid exchange accounts were created',
            'account: %s\\%s' % (domain, username),
            'email addresses: %s' % ', '.join(email_addresses), ])
        return None

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

    def __init__(
            self,
            subject=None, accounts=None, email_addresses=None, logger=None):
        """
        constructor

        :arg list accounts: a list of :class:`<exchangelib.Account>` objects

        :arg list email_addresses:

            the list SMTP aliases,  i.e. the Exchange accounts for this
            particular user

        :arg logger: windows events log writer
        :argtype logger: :class:`<logger.WinLogEvent>`
        """
        if subject is None:
            subject = get_config().get('email_subject')
        self.messages = []

        if logger is None:
            logger = LogWinEvent()

        self.logger = logger

        if accounts is None:
            accounts = get_accounts(logger=self.logger)

        self.accounts = accounts

        if not self.accounts:
            # stop wasting time
            return

        if not isinstance(accounts, list):
            raise TypeError(
                'bad object type %s. must be a list' % type(accounts))

        if email_addresses is None:
            email_addresses = get_config().get('email_addresses')

        self.emails = []
        for email_address in email_addresses:
            self.emails.append(
                validate_email_to_ascii(email_address, logger=self.logger))

        if not self.emails:
            return

        for account in accounts:
            if not isinstance(account, Account):
                raise TypeError(
                    'bad object type %s for %s. must be exchangelib.Account' %
                    (type(account), str(account)))

        self.accounts = accounts

        for account in self.accounts:
            message_body = str(uuid4())
            self.messages.append(
                WitnessMessage(
                    message_uuid=message_body,
                    account_for_message=Message(account=account,
                                                subject=subject,
                                                body=message_body,
                                                to_recipients=self.emails)
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
