"""
.. _mailer:

mail module for exchange monitoring borg bots

:module:    mail_borg.mailer

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    may 14, 2019

This module provides a client library for accessing an
`Exchange Web Services (EWS) 
<https://searchwindowsserver.techtarget.com/definition/Exchange-Web-Services-EWS>`_
end point.

This client provides strictly email functionality:

* ``connect`` to an Exchange server over EWS

* ``send`` an email via an Exchange server over EWS

* ``receive`` the email via an Exchange server over EWS

The ``send`` and ``receive`` terms are somewhat misleading. A ``send`` is
better described as *we are creating an artifact that looks like an email
message on an Exchange server*. A ``receive`` is more or less the equivalent
of *we are accessing an artifact that looks like an email message on an
Exchange server*.

.. note::

    We have made a conscious effort to avoid using list comprehensions because
    of how exceptions need to be handled in this module.

    Specifically, if there is a problem with a list item, we want to log the
    problem and continue processing. That is not supported with list
    comprehensions; if an exception occurs, processing will be stopped even if
    we catch the error.

Most members of this module make use of an attribute named
``config``. This attribute is the Python representation of the structure
described in the :ref:`borg_client_config`.

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
from exchangelib import (
    ServiceAccount, Message, Account, Configuration, DELEGATE,
)
from exchangelib.errors import ErrorTooManyObjectsOpened
from retry import retry

from config import load_config
from logger import LogWinEvent


class _Logger():
    """
    Custom logging class that will write to the windows event log, and to
    a GUI window text control if access to one such destination is provided

    When working with GUI applications, the :mod:`mail_borg.mailer` modules
    needs to run on a thread separate from the one where the GUI application
    is running. Communication between these threads is provided via a
    :class:`queue.Queue` instance.

    """

    def __init__(self, update_window_queue=None, event_logger=None):
        """
        :arg ``queue.Queue`` update_window_queue:

            a queue object used to pass updates to a GUI running in
            the main thread. this argument is not mandatory.

        :arg event_logger:

            an instance of the :class:`mail_borglogger.LogWinEvent`

            if one is not provided, the constructor will create it
        """
        self.console_logger = update_window_queue
        """
        instance attribute storing the :class:`queue.Queue` instance used
        for passing data to a GUI application
        """
        if event_logger is None:
            event_logger = LogWinEvent()

        self.event_logger = event_logger
        """
        instance attribute storing the :class:`mail_borglogger.LogWinEvent`
        instance used to create Windows log events
        """

    def info(self, strings):
        """
        write info level events

        :arg strings: an `object` that can be serialized to ``JSON``
        """
        self.event_logger.info(strings=[json.dumps(strings)])
        self.update_console(strings, level='INFO')

    def warn(self, strings):
        """
        write warn level events

        :arg strings: an `object` that can be serialized to ``JSON``
        """
        self.event_logger.warn(strings=[json.dumps(strings)])
        self.update_console(strings, level='WARN')

    def err(self, strings):
        """
        write error level events

        :arg strings: an `object` that can be serialized to ``JSON``
        """
        self.event_logger.err(strings=[json.dumps(strings)])
        self.update_console(strings, level='ERROR')

    def update_console(self, strings, level=None):
        """
        update the GUI window control with the logged message

        this method will update the `queue.Queue` used to communicate with
        the GUI application

        :arg strings: an `object` than can be cast to `str`

        :arg str level: INFO|WARN|ERROR, default is INFO
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
    """

    :arg config:

        a copy of the :attr:`WitnessMessages.config`  instance attribute

    :returns: a ``DOMAIN\\username`` account representation
    :rtype: :class:`str`
    """
    return '{}\\{}'.format(config.get('domain'), config.get('username'))


def validate_email_to_ascii(email_address, logger=None, **config):
    """
    this function is using the `python-email-validator 
    <https://github.com/JoshData/python-email-validator>`_ package to
    return a valid email address

    Optionally:

    * reject an email address  the username part contains non `ASCII 
      <https://www.cs.cmu.edu/~pattis/15-1XX/common/handouts/ascii.html>`_
      characters

      If one wants to support UTF-8 characters, one must make sure that the
      Exchange server supports `SMTPUTF8 
      <https://tools.ietf.org/html/rfc6531>`_

    * support `Internationalized domain names(RFC 5891) 
      <https://tools.ietf.org/html/rfc5891>`_

    * normalize usernames to ASCII

      .. todo:: `<https://trello.com/c/bkfFT4Cv>`_

    * verify the existence of the MX record for the email domain. there is
      a configurable timeout argument for this option

    The options are provided via the ``config`` argument.

    :arg str email_address: the email address to validate

    :arg config:

        a copy of the :attr:`WitnessMessages.config`  instance attribute

    :arg logger: log all problems

        Usually provided by the caller the logger data is provided by the
        calling function but this function is capable of creating a
        :class:`_Logger` instance if needed

    :type logger: :class:`_Logger`

    :returns:

        a valid, normalized email address value or ``None`` if the
        validation fails. see the :raises: section for a discussion about this

    :raises:

        This function doesn't raise any exceptions because it does its own
        error handling. It is catching and logging:

        :exc:``email_validator.EmailSyntaxError``

        :exc:``email_validator.EmailUndeliverableError``

    """
    if not config:
        config = load_config()

    if logger is None:
        logger = _Logger()

    try:
        email_dict = validate_email(
            email_address,
            allow_smtputf8=config.get('exchange_client_config').
            get('utf8_address'),
            timeout=config.get('exchange_client_config').
            get('check_mx_timeout'),
            allow_empty_local=False,
            check_deliverability=config.get('exchange_client_config').
            get('check_mx'))
    except (EmailSyntaxError, EmailUndeliverableError) as error:
        logger.warn(
            dict(type='configuration', status='FAIL',
                 wm_id=config.get('wm_id'),
                 account=email_address,
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

    accounts = []

    exchange_accounts = config.get('exchange_client_config').\
        get('exchange_accounts')
    for exchange_account in exchange_accounts:
        if not validate_email_to_ascii(
                exchange_account.get('smtp_address'), logger=logger, **config):
            continue

        credentials = ServiceAccount(
            username='{}\\{}'.format(
                exchange_account.get('domain_account').get('domain'),
                exchange_account.get('domain_account').get('username')),
            password=exchange_account.get('domain_account').get('password')
        )

        exc_config = None
        if not exchange_account.get('exchange_autodiscover', True):
            exc_config = Configuration(
                server=exchange_account.get('autodiscover_server'),
                credentials=credentials)

        try:
            if exchange_account.get('exchange_autodiscover', True):
                accounts.append(Account(
                    primary_smtp_address=exchange_account.get('smtp_address'),
                    credentials=credentials,
                    autodiscover=True,
                    access_type=DELEGATE))
            else:
                accounts.append(Account(
                    primary_smtp_address=exchange_account.get('smtp_address'),
                    config=exc_config,
                    autodiscover=False,
                    access_type=DELEGATE))
            logger.info(
                dict(type='connection', status='PASS',
                     wm_id=config.get('wm_id'),
                     message='connected to exchange',
                     account='{}\\{}, {}'.format(
                         exchange_account.get('domain_account').get('domain'),
                         exchange_account.get(
                             'domain_account').get('username'),
                         exchange_account.get('smtp_address')))
            )
        except Exception as err:  # pylint: disable=broad-except
            logger.err(
                dict(type='connection', status='FAIL',
                     wm_id=config.get('wm_id'),
                     message='cannot connect to exchange',
                     account='{}\\{}, {}'.format(
                         exchange_account.get('domain_account').get('domain'),
                         exchange_account.get(
                             'domain_account').get('username'),
                         exchange_account.get('smtp_address')),
                     exeption=str(err))
            )

    if not accounts:
        logger.err(
            dict(type='configuration', status='FAIL',
                 wm_id=config.get('wm_id'),
                 account=None,
                 message=(
                     'no valid exchange account found in config for bot %s'
                     % config.get('host_name')))
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
        self._abort = False

        if not config:
            config = load_config()

        self.config = config

        self.config['wm_id'] = '{}+{}+{}'.format(
            self.config.get('site').get('site', 'no_site'),
            socket.gethostname(),
            datetime.now(tz=get_localzone())
        )

        self.messages = []

        self.update_window_queue = console_logger

        self.logger = _Logger(
            update_window_queue=console_logger, event_logger=logger)

        if accounts is None:
            accounts = get_accounts(logger=self.logger, **config)

        if not accounts:
            self._abort = True
            return

        if not isinstance(accounts, list):
            raise TypeError(
                'bad object type %s. must be a list' % type(accounts))

        for account in accounts:
            if not isinstance(account, Account):
                self.logger.err(
                    dict(type='configuration', status='FAIL',
                         wm_id=self.config.get('wm_id'),
                         account=str(account),
                         message='could not create any messages')
                )

        self.accounts = accounts

        if not self.accounts:
            # stop wasting time
            self._abort = True
            return

        self.witness_emails = []
        if self.config.get('exchange_client_config').get('witness_addresses'):
            for witness_address in self.config.get('exchange_client_config').\
                    get('witness_addresses'):
                self.witness_emails.append(
                    validate_email_to_ascii(
                        witness_address, logger=self.logger, **config))

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
        tags = '{}[{}][{}]{}'.format(
            self.config.get('exchange_client_config').get('tags'),
            self.config.get('site').get('site'), socket.gethostname(),
            self.config.get('exchange_client_config').get('email_subject')
        )

        if self.config.get('exchange_client_config').get('debug'):
            tags = '[DEBUG]{}'.format(tags)

        return tags

    def send(self):
        """
        send out the exchange monitoring messages

        if there are no messages, log an error

        if sending a particular message raises an error,
        log it and keep sending
        """
        if self._abort:
            if self.update_window_queue:
                self.update_window_queue.put_nowait(('abort',))

            return 'mail check abort'

        if not self.messages:
            self.logger.err(
                dict(type='create', status='FAIL',
                     wm_id=self.config.get('wm_id'),
                     account=None,
                     message=(
                         'could not create any messages with the'
                         ' config of bot %s' % self.config.get('host_name')))
            )
            return 'nothing to send'

        # we need to purge the messages that we cannot send, thus
        messages = self.messages
        for message in messages:
            try:
                message.message.send()

                self.logger.info(
                    dict(type='send', status='PASS',
                         wm_id=self.config.get('wm_id'),
                         account=message.account_for_message.
                         primary_smtp_address,
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
                         account=message.account_for_message.
                         primary_smtp_address,
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

        return 'sent'

    def verify_receive(self, min_wait_receive=None, step_wait_receive=None,  # pylint: disable=too-many-branches
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
            min_wait_receive = int(
                self.config.get(
                    'exchange_client_config').get('min_wait_receive'))

        if step_wait_receive is None:
            step_wait_receive = int(
                self.config.get(
                    'exchange_client_config').get('backoff_factor'))

        if max_wait_receive is None:
            max_wait_receive = int(
                self.config.get(
                    'exchange_client_config').get('max_wait_receive'))

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

        if self._abort:
            if self.update_window_queue:
                self.update_window_queue.put_nowait(('abort',))

            return 'mail check abort'

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
                         account=message.account_for_message.
                         primary_smtp_address,
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
                                     account=message.
                                     account_for_message.primary_smtp_address,
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
                         account=message.account_for_message.
                         primary_smtp_address,
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

                if not self.config.get('exchange_client_config').get('debug'):
                    found_message.delete()

                continue

            else:
                self.logger.err(
                    dict(type='receive', status='FAIL',
                         wm_id=self.config.get('wm_id'),
                         account=message.account_for_message.
                         primary_smtp_address,
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
