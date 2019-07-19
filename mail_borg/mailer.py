"""
.. _mailer:

mail module for exchange monitoring borg bots

:module:    mail_borg.mailer

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    may 14, 2019

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
import json
import socket
import time

from datetime import datetime
from uuid import uuid4

from tzlocal import get_localzone
from email_validator import (
    validate_email, EmailSyntaxError, EmailUndeliverableError,
)
from exchangelib import ServiceAccount, Message, Account, Configuration
from exchangelib.errors import ErrorTooManyObjectsOpened
from retry import retry

from config import load_config
from logger import LogWinEvent


class _Logger():
    """
    custom logger class that will write to the windows event log and to
    a GUI window text control if one is provided
    """

    def __init__(self, update_window_queue=None, event_logger=None):
        """
        :arg ``queue.Queue`` update_window_queue:

            a queue object used to pass updates to a GUI running in
            the main thread. this argument is not mandatory.

        :arg event_logger:

            an instance of the :class:`<logger.LogWinEvent>`

            if one is not provided, the constructor will create it
        """
        self.console_logger = update_window_queue
        if event_logger is None:
            event_logger = LogWinEvent()

        self.event_logger = event_logger

    def info(self, strings):
        """
        write info level events
        """
        self.event_logger.info(strings=[json.dumps(strings)])
        self.update_console(strings, level='INFO')

    def warn(self, strings):
        """
        write warn level events
        """
        self.event_logger.warn(strings=[json.dumps(strings)])
        self.update_console(strings, level='WARN')

    def err(self, strings):
        """
        write error level events
        """
        self.event_logger.err(strings=[json.dumps(strings)])
        self.update_console(strings, level='ERROR')

    def update_console(self, strings, level=None):
        """
        update the GUI window control with the logged message
        """
        if self.console_logger is None:
            return

        if self.console_logger.full():
            return

        if level is None:
            level = 'INFO'

        self.console_logger.put_nowait(
            ('output', '[{}] {:%X}: {}\n'.format(level,
                                                 datetime.now(), strings))
        )


def _get_account(config):
    return '{}\\{}'.format(config.get('domain'), config.get('username'))


def validate_email_to_ascii(email_address, logger=None, **config):
    """
    validate, normalize, and return an email address
    optionally also convert it to ascii

    :arg dict config:

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

    :arg logger: log all problems; usually provided by the caller
    :argtype logger: :class:`<_Logger>`

    :returns:

        a valid, normalized email address value or ``None`` if the
        validation fails. see the :raises: section for a discussion about this

    :raises:

        this function doesn't raise any exceptions because it does its own
        error handling by logging specific failures to the windows events log
    """
    if not config:
        config = load_config()

    if logger is None:
        logger = _Logger()

    try:
        email_dict = validate_email(
            email_address, allow_smtputf8=config.get('allow_utf8_email'),
            timeout=config.get('check_mx_timeout'),
            allow_empty_local=False,
            check_deliverability=config.get('check_email_mx'))
    except (EmailSyntaxError, EmailUndeliverableError) as error:
        logger.warn(
            dict(type='configuration', status='FAIL',
                 wm_id=config.get('wm_id'),
                 account='{}, {}'.format(_get_account(config), email_address),
                 message='bad email address %s' % email_address,
                 exception=str(error))
        )
        return None

    if config.get('force_ascii_email'):
        return email_dict.get('email_ascii')

    return email_dict.get('email')


def get_accounts(logger=None, **config):
    """
    get a list of Exchange accounts

    the assumption is that the same domain account has multiple
    Exchange accounts and that we want to verify all these accounts

    :arg dict config:

        :arg str domain: the windows domain

        :arg str username: the domain user name

        :arg str password: the password

        :arg list email_addresses:

            the list SMTP aliases,  i.e. the Exchange accounts for this
            particular user

    :arg logger: logger; usually provided by the caller
    :argtype logger: :class:`<logger.WinLogEvent>`

    """
    if not config:
        config = load_config()

    if logger is None:
        logger = _Logger()

    emails = []
    for email_address in config.get('email_addresses').split(','):
        emails.append(validate_email_to_ascii(
            email_address, logger=logger, **config))

    if not emails:
        logger.err(
            dict(type='configuration', status='FAIL',
                 wm_id=config.get('wm_id'),
                 account=_get_account(config),
                 message='no valid email addresses found in %s'
                 % config.get('email_addresses'))
        )
        return None

    credentials = ServiceAccount(
        username='{}\\{}'.format(config.get('domain'), config.get('username')),
        password=config.get('password'))

    exc_config = None
    if not config.get('autodiscover', True):
        exc_config = Configuration(server=config.get('exchange_server'),
                                   credentials=credentials)

    accounts = []
    for email in emails:
        try:
            if config.get('autodiscover', True):
                accounts.append(Account(primary_smtp_address=email,
                                        credentials=credentials,
                                        autodiscover=True))
            else:
                accounts.append(Account(primary_smtp_address=email,
                                        config=exc_config,
                                        autodiscover=False))
            logger.info(
                dict(type='connection', status='PASS',
                     wm_id=config.get('wm_id'),
                     message='connected to exchange',
                     account='{}\\{}, {}'.format(
                         config.get('domain'), config.get('username'), email))
            )
        except Exception as err:  # pylint: disable=broad-except
            logger.err(
                dict(type='connection', status='FAIL',
                     wm_id=config.get('wm_id'),
                     message='cannot connect to exchange',
                     account='{}\\{}, {}'.format(
                         config.get('domain'), config.get('username'), email),
                     exeption=str(err))
            )

    if not accounts:
        logger.err(
            dict(type='configuration', status='FAIL',
                 wm_id=config.get('wm_id'),
                 message='no valid exchange account found',
                 account=_get_account(config))
        )
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


class WitnessMessages():  # pylint: disable=too-many-instance-attributes
    """
    class for sent and received messages

    a message is an ``uuid`` instance generated via : method:`<uuid.uuid4>`.
    this way each message has/is its own unique identifier and can be searched
    for in the inbox. the identifier must be aprt of the message subject;
    there is a problem with fuzzy searching in the body on the Exchange side

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
            self, accounts=None, logger=None, console_logger=None, **config):
        """
        constructor

        :arg list accounts: a list of :class:`<exchangelib.Account>` objects

        :arg dict config:


            :arg str domain: the windows domain

            :arg str username: the domain user name

            :arg str password: the password

            :arg list email_addresses:

                the list SMTP aliases,  i.e. the Exchange accounts for this
                particular user. also used as the list of send to emails.
                this may have to change

            :arg list witness_addresses:

                cc the message(s) to human monitored mailboxes if desired

            :arg str email_subject:

            :arg str site:

            :arg str tags:

            :arg bool debug:

            all the args required for the :function:`<validate_email_to_ascii>`

        :arg logger: windows events log writer
        :argtype logger: :class:`<logger.WinLogEvent>`
        """
        self._sent = False

        if not config:
            config = load_config()

        self.config = config

        self.config['wm_id'] = '{}+{}+{}'.format(
            self.config.get('site', 'no_site'), socket.gethostname(),
            datetime.now(tz=get_localzone())
        )

        self.messages = []

        self.update_window_queue = console_logger

        self.logger = _Logger(
            update_window_queue=console_logger, event_logger=logger)

        if accounts is None:
            accounts = get_accounts(logger=self.logger, **config)

        self.accounts = accounts

        if not self.accounts:
            # stop wasting time
            return

        if not isinstance(accounts, list):
            raise TypeError(
                'bad object type %s. must be a list' % type(accounts))

        self.emails = []
        for email_address in self.config.get('email_addresses').split(','):
            self.emails.append(
                validate_email_to_ascii(
                    email_address, logger=self.logger, **config))

        if not self.emails:
            # again, stop wasting time
            return

        self.witness_emails = []
        if self.config.get('witness_addresses'):
            for witness_address in \
                    self.config.get('witness_addresses').split(','):
                self.witness_emails.append(
                    validate_email_to_ascii(
                        witness_address, logger=self.logger, **config))

        for account in accounts:
            if not isinstance(account, Account):
                raise TypeError(
                    'bad object type %s for %s. must be exchangelib.Account' %
                    (type(account), str(account)))

        self.accounts = accounts
        for account in self.accounts:
            message_uuid = str(uuid4())
            message_body = 'message_group_id: {}, message_id: {}'.\
                format(self.config.get('wm_id'), message_uuid)
            self.messages.append(
                WitnessMessage(
                    message_uuid=message_uuid,
                    message=Message(
                        account=account,
                        subject='{} {}'.format(
                            self._set_subject(), message_body),
                        body=message_body,
                        to_recipients=[
                            account.primary_smtp_address],
                        cc_recipients=self.witness_emails),
                    account_for_message=account
                )
            )

    def _set_subject(self):
        """
        add various tags as well as site and bot info to the email subject
        """
        tags = '[DEBUG]' if self.config.get('debug') else ''
        tags += '[{}]'.format(
            self.config.get('site')) if self.config.get('site') else ''
        tags = '{}[{}]'.format(tags, socket.gethostname())

        return '{}{}'.format(tags, self.config.get('email_subject',
                                                   'email canary'))

    def send(self):
        """
        send out the exchange monitoring messages

        if there are no messages, log an error

        if sending a particular message raises an error,
        log it and keep sending
        """
        if not self.messages:
            self.logger.err(
                dict(type='create', status='FAIL',
                     wm_id=self.config.get('wm_id'),
                     account=_get_account(self.config),
                     message='could not create any messages')
            )
            return

        # we need to purge the messages that we cannot send, thus
        messages = self.messages
        for message in messages:
            try:
                message.message.send()

                self.logger.info(
                    dict(type='send', status='PASS',
                         wm_id=self.config.get('wm_id'),
                         account='{}, {}'.format(
                             _get_account(self.config),
                             message.account_for_message.primary_smtp_address),
                         message='monitoring message sent',
                         message_uuid=str(message.message_uuid),
                         from_email=message.
                         account_for_message.primary_smtp_address,
                         to_emails=', '.join([r.email_address for r in
                                              message.message.to_recipients]))
                )

            except Exception as error:  # pylint: disable=broad-except
                self.logger.err(
                    dict(type='send', status='FAIL',
                         wm_id=self.config.get('wm_id'),
                         account='{}, {}'.format(
                             _get_account(self.config),
                             message.account_for_message.primary_smtp_address),
                         message='cannot send message',
                         message_uuid=str(message.message_uuid),
                         from_email=message.
                         account_for_message.primary_smtp_address,
                         to_emails=', '.join([r.email_address for r in
                                              message.message.to_recipients]),
                         exception=str(error))
                )

                self.messages.remove(message)

        self._sent = True

    def verify_receive(self, min_wait_receive=None, step_wait_receive=None,
                       max_wait_receive=None):
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

        """
        if min_wait_receive is None:
            min_wait_receive = int(self.config.get('min_wait_receive'))

        if step_wait_receive is None:
            step_wait_receive = int(self.config.get('step_wait_receive'))

        if max_wait_receive is None:
            max_wait_receive = int(self.config.get('max_wait_receive'))

        class ErrorMessageNotFound(Exception):
            """
            custom exception to be raised in case a message is not found
            """

        @retry((ErrorTooManyObjectsOpened, ErrorMessageNotFound),
               delay=int(min_wait_receive), max_delay=int(max_wait_receive),
               backoff=int(step_wait_receive))
        def get_from_inbox(message):
            found_message = message.account_for_message.inbox.filter(
                subject__icontains=str(message.message_uuid))

            if found_message.exists():
                return found_message.get()

            raise ErrorMessageNotFound()

        if not self._sent:
            self.send()

        time.sleep(min_wait_receive)
        for message in self.messages:

            try:
                found_message = get_from_inbox(message)
            except ErrorTooManyObjectsOpened as error:
                self.logger.err(
                    dict(type='receive', status='FAIL',
                         wm_id=self.config.get('wm_id'),
                         account='{}, {}'.format(
                             _get_account(self.config),
                             message.account_for_message.primary_smtp_address),
                         message=(
                             'too many objects opened on the server,'
                             ' please increase the Check Receive Timeout'
                             ' value'),
                         message_uuid=str(message.message_uuid),
                         exception=str(error),
                         from_email=message.
                         account_for_message.primary_smtp_address,
                         to_emails=', '.join(
                             [r.email_address for r in
                              message.message.to_recipients]))
                )
                continue
            except ErrorMessageNotFound:
                found_message = None
            except Exception as error:  # pylint: disable=broad-except
                self.logger.err(dict(type='receive', status='FAIL',
                                     wm_id=self.config.get('wm_id'),
                                     account='{}, {}'.format(
                                         _get_account(self.config),
                                         message.account_for_message.primary_smtp_address),
                                     message=(
                                         'unexpected error while checking for'
                                         ' message received'),
                                     message_uuid=str(message.message_uuid),
                                     exception=str(error),
                                     from_email=message.
                                     account_for_message.primary_smtp_address,
                                     to_emails=', '.join(
                                         [r.email_address for r in
                                          message.message.to_recipients]))
                                )
                continue

            if found_message:
                self.logger.info(
                    dict(type='receive', status='PASS',
                         wm_id=self.config.get('wm_id'),
                         account='{}, {}'.format(
                             _get_account(self.config),
                             message.account_for_message.primary_smtp_address),
                         message='message received',
                         message_uuid=str(message.message_uuid),
                         from_address=found_message.author.
                         email_address,
                         to_addresses=', '.join(
                             [mailbox.email_address for
                                      mailbox in found_message.to_recipients]),
                         created=str(found_message.datetime_created),
                         sent=str(found_message.datetime_sent),
                         received=str(found_message.datetime_received),
                         from_email=message.
                         account_for_message.primary_smtp_address,
                         to_emails=', '.join(
                             [r.email_address for r in
                              message.message.to_recipients]))
                )

                if not self.config.get(
                        'debug',
                        load_config().get('debug', True)):
                    found_message.delete()

                continue

            else:
                self.logger.err(
                    dict(type='receive', status='FAIL',
                         wm_id=self.config.get('wm_id'),
                         account='{}, {}'.format(
                             _get_account(self.config),
                             message.account_for_message.primary_smtp_address),
                         message='message received',
                         message_uuid=str(message.message_uuid),
                         from_email=message.
                         account_for_message.primary_smtp_address,
                         to_emails=', '.join(
                             [r.email_address for r in
                              message.message.to_recipients]))
                )

        if self.update_window_queue:
            self.update_window_queue.put_nowait(('control',))
