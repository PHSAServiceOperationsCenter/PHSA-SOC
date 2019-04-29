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
import time
from uuid import uuid4

from email_validator import (
    validate_email, EmailSyntaxError, EmailUndeliverableError,
)
from exchangelib import ServiceAccount, Message, Account

from config import get_config
from logger import LogWinEvent


def validate_email_to_ascii(  # pylint: disable=too-many-arguments
        email_address, to_ascii=True, allow_smtputf8=False,
        check_deliverability=True,
        timeout=get_config().get('check_mx_timeout', 15), logger=None):
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

    :arg int timeout: seconds, default picked from config, fallback 15

        timeout value for verifying the MX record of the email address

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
            email_address, allow_smtputf8=allow_smtputf8, timeout=timeout,
            allow_empty_local=False, check_deliverability=check_deliverability)
    except (EmailSyntaxError, EmailUndeliverableError) as error:
        logger.warn(strings=[
            'type: verify configuration',
            'status: FAIL',
            'status message: bad email address %s' % email_address,
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
        logger.err(
            strings=[
                'type: verify configuration',
                'status: FAIL',
                'status message: none of the %s email addresses is valid.'
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
                    'type: verify connection',
                    'status: PASS',
                    'status message: connected to exchange with'
                    ' account %s\\%s, %s' % (domain, username, email), ])
        except Exception as err:  # pylint: disable=broad-except
            logger.err(
                strings=[
                    'type: verify connection',
                    'status: FAIL',
                    'message: cannot connect to exchange with'
                    'account %s\\%s, %s' % (domain, username, email),
                    'exception: %s' % str(err), ])

    if not accounts:
        logger.error(strings=[
            'type: verify configuration',
            'status: FAIL',
            'status message: invalid exchange configuration for all'
            'accounts in %s\\%s' % (domain, username),
            'email addresses: %s' % ', '.join(email_addresses), ])
        return None

    return accounts


WitnessMessage = collections.namedtuple(
    'WitnessMessage', ['message_uuid', 'message', 'account_for_message'])
"""
:var WitnessMessage: name tuple class describing an exchange message

    *    :message_uuid: an unique identifier for the message
                        used for retrieving the message from the inbox
                        so as to verify that it was received

    *    :message: the message itself

    *    :account_for_message: the exchange account used to send the
                               message

:vartype WitnessMessage: :class:`<collections.namedtuple>`
"""


def _get_logger(logger):
    if logger is None:
        logger = LogWinEvent()
    return logger


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

    def __init__(  # pylint: disable=too-many-arguments
            self,
            subject=None, accounts=None, email_addresses=None,
            witness_addresses=None, logger=None):
        """
        constructor

        :arg list accounts: a list of :class:`<exchangelib.Account>` objects

        :arg list email_addresses:

            the list SMTP aliases,  i.e. the Exchange accounts for this
            particular user

        :arg logger: windows events log writer
        :argtype logger: :class:`<logger.WinLogEvent>`
        """
        self._sent = False

        if subject is None:
            subject = get_config().get('email_subject')
        self.messages = []

        self.logger = _get_logger(logger)

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
            # again, stop wasting time
            return

        if witness_addresses is None:
            witness_addresses = get_config().get('witness_addresses')

        self.witness_emails = []
        for witness_address in witness_addresses:
            self.witness_emails.append(
                validate_email_to_ascii(witness_address, logger=self.logger))

        for account in accounts:
            if not isinstance(account, Account):
                raise TypeError(
                    'bad object type %s for %s. must be exchangelib.Account' %
                    (type(account), str(account)))

        self.accounts = accounts

        for account in self.accounts:
            message_body = uuid4()
            self.messages.append(
                WitnessMessage(
                    message_uuid=message_body,
                    message=Message(account=account,
                                    subject='{} with identifier {}'.format(
                                        subject, message_body),
                                    body=message_body,
                                    to_recipients=self.emails,
                                    cc_recipients=self.witness_emails),
                    account_for_message=account
                )
            )

    def send(self):
        """
        send out the exchange monitoring messages

        if there are no messages, log an error

        if sending a particular message raises an error,
        log it and keep sending
        """
        if not self.messages:
            self.logger.err(
                strings=[
                    'type: verify configuration',
                    'status: FAIL',
                    'status message:'
                    ' it was not possible to create any monitoring'
                    ' messages. please double-check the exchange configuration'
                    ' for this node.', ])
            return

        # we need to purge the messages that we cannot send, thus
        messages = self.messages
        for message in messages:
            try:
                message.message.send()

                self.logger.info(
                    strings=[
                        'type: verify send',
                        'status: PASS',
                        'status message: monitoring message sent',
                        'message_uuid: %s' % message.message_uuid,
                        'account: %s'
                        % message.account_for_message.primary_smtp_address,
                        'to: %s'
                        % ', '.join(
                            [r.email_address for r in
                             message.message.to_recipients]), ])

            except Exception as error:  # pylint: disable=broad-except
                self.logger.err(
                    strings=[
                        'type: verify send',
                        'status: FAIL',
                        'status message: cannot send monitoring message',
                        'message_uuid: %s' % message.message_uuid,
                        'account: %s'
                        % message.account_for_message.primary_smtp_address,
                        'to: %s'
                        % ', '.join(
                            [r.email_address for r in
                             message.message.to_recipients]),
                        'error: %s' % str(error), ])

                self.messages.remove(message)

        self._sent = True

    def verify_receive(
        self,
            min_wait_receive=get_config().get('min_wait_receive', 3),
            step_wait_receive=get_config().get('step_wait_receive', 3),
            max_wait_receive=get_config().get('max_wait_receive', 120)):
        """
        look for all the messages that were sent in the inbox of each account
        used to send them

        each message is sent from the account associated with said message
        to each address in the send_to attribute.
        additionally, each address in the send_to attribute is associated
        with an account that is being monitored.
        thus we wait a while, then

        * for each account:

          * open the account.inbox and search for each message by uuid

            * if found log the sent_at, received_at for further analysis

            * if not found log an error:
              cannot communicate from message.account.smtp_address
              to account.inboc.smtp_adddress

        :arg int wait_receive: seconds, default picked from config

            fallback 60 seconds;
            time to wait before looking for the messages since exchange is not
            all that fast

        #TODO: see https://github.com/ecederstrand/exchangelib/issues/581
        # maybe some poor soul will come up with a solution to make the
        # wait dynamic
        """
        if not self._sent:
            self.send()

        time.sleep(min_wait_receive)

        for account in self.accounts:
            for message in self.messages:

                _wait_receive = min_wait_receive

                found_message = account.inbox.filter(
                    subject__icontains=str(message.message_uuid))

                while _wait_receive < max_wait_receive:

                    if found_message.exists():

                        found_message = found_message.get()
                        self.logger.info(
                            strings=[
                                'type: transmission verification',
                                'status: PASS',
                                'status message:'
                                ' email message successfully sent and received',
                                'message_uuid: %s' % message.message_uuid,
                                'from domain: %s'
                                % found_message.author.
                                email_address.split('@')[1],
                                'to domains: %s'
                                % ', '.join(
                                    [
                                        mailbox.email_address.split('@')[1] for
                                        mailbox in found_message.to_recipients
                                    ]),
                                'created: %s' % found_message.datetime_created,
                                'sent: %s' % found_message.datetime_sent,
                                'received: %s'
                                % found_message.datetime_received,
                                'wait_receive: %s' % _wait_receive, ])

                        found_message.delete()

                        break

                    time.sleep(step_wait_receive)
                    _wait_receive = _wait_receive + step_wait_receive

                else:
                    self.logger.err(
                        strings=[
                            'type: transmission verification',
                            'status: FAIL',
                            'status message: message was not received',
                            'message_uuid: %s' % message.message_uuid,
                            'from: %s'
                            % message.account_for_message.
                            primary_smtp_address.split('@')[1],
                            'to: %s'
                            % account.primary_smtp_address.split('@')[1],
                            'wait_receive: %s' % _wait_receive, ])
