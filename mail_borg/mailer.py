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

    The methods in this class that take a ``strings`` argument expect that
    said argument is can be serialized to ``JSON``.
    The reason for this requirement is architectural in nature; somewhere down
    the line these messages will put on a wire and the end points expect to
    be receive ``JSON`` objects.

    As used in the :ref:`Mail Borg Client Application`, all the messages fed
    into an instance of this class are Python :class:`dictionaries <dict>`
    with the following structure:

    .. code-block:: python

        msg = {
                'type': 'the type of the event',
                'status': 'is it a PASS or a FAIL',
                'wm_id': 'unique identifier for the message group',
                'message': 'an explanation for the event',
                'exception': 'the exception that triggered the event, if any',
        }

    The message group maps to an single Exchange verification operation. All
    the messages that are part of the verification operation include the
    ``wm_id`` attribute. This attribute is essential for various operations
    executed on the server side/

    All the values in this dictionary must be :class:`strings <str>`.

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

        a :class:`dictionary <dict>` that matches the structure described in
        :ref:`borg_client_config` (or the relevantr portions thereof)

        As used in the :ref:`Mail Borg Client Application`, the ``config``
        argument is provided via an :attr:`WitnessMessages.config` instance
        attribute

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

        a :class:`dictionary <dict>` that matches the structure described in
        :ref:`borg_client_config` (or the relevantr portions thereof)

        As used in the :ref:`Mail Borg Client Application`, the ``config``
        argument is provided via an :attr:`WitnessMessages.config` instance
        attribute

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
    get a list of working Exchange accounts

    This function expects that each Exchange account is described by the
    ``config`` argument as shown in the ``JSON`` snippet below.

    A full representation of the structure of the ``config`` argument as
    used in the :ref:`Mail Borg Client Application` is available in the
    :ref:`borg_client_config` section.

    .. code-block:: json

        {
            "smtp_address":"z-spexcm001-db01001@phsa.ca",
            "domain_account":
                {
                    "domain":"PHSABC",
                    "username":"svc_SOCmailbox",
                    "password":"goodluckwiththat"
                },
                "exchange_autodiscover":true,
                "autodiscover_server":null
        }

    :arg dict config:

       a :class:`dictionary <dict>` that matches the structure described in
       :ref:`borg_client_config` (or the relevant portions thereof)

       As used in the :ref:`Mail Borg Client Application`, the ``config``
       argument is provided via an :attr:`WitnessMessages.config` instance
       attribute

    :arg logger:

        logging facility; Usually provided by the caller the logger
        data is provided by the calling function but this function is capable
        of creating a :class:`_Logger` instance if needed

    :type logger: :class:`_Logger`


    :returns:
        :class:`list` of :class:`exchangelib.Account` objects
        An :class:`exchangelib.Account` object is only created if this
        module was able to connect to the EWS end point using the provided
        credentials.

        If an Exchange account entry in the ``config`` argument cannot be used
        to create a valid :class:`exchangelib.Account` instance, an error
        will be logged and there will be no matching entry in the return.

        If none of the Exchange account entries in the ``config`` argument can
        be used to create a valid :class:`exchangelib.Account` instance,
        an error will be logged and the function will return ``None``

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
class describing an exchange message created using the
:func:`collections.namedtuple` factory function

"""


class WitnessMessages():
    """
    Class that encapsulates all the functionality required to execute
    an Exchange verification operation once

    An Exchange verification operation consists of sending a message to self
    for each Exchange account listed in the ``config`` attribute.
    The verification itself has three components that must all be successful

    * connecting successfully to the Exchange server

    * sending the message successfully

    * finding the sent message in the receiving ``inbox`` successfully


    The main attribute in this class is the Exchange message.
    Each Exchange message contains an ``uuid`` instance generated
    via the :meth:`<uuid.uuid4>` method in the subject line.
    This way we can search the receiving ``inbox`` for each send message.
    The identifier must be part of the message subject because
    there is a problem with fuzzy searching in the message body on the EWS
    side.
    The class constructor is responsible for creating this identifier.

    Each instance of this class will also create an unique instance identifier.
    This identifier is appended to both the email message itself and,
    more importantly, to the Windows log events created while said class
    instance is active.
    This identifier is used to figure out the site and the bot from whence
    the log event was collected and the time when when the event was created.
    This identifier is created in the constructor and will become part of
    the :class:`dictionary <dict>` stored in the :attr:`config` instance
    attribute with a key of ``wm_id``.
    The format of this identifier is ``$site+$host+local_timestamp`` where
    $site is the :class:`mail_collector.models.MailSite` site where the
    client is running and $host is the name of the bot as returned by the
    :meth:`socket.gethostname` method.

    This class builds a separate `exchangelib.Message` for each Exchange
    account defined in the ``config`` argument. See :func:`get_accounts` for
    details about the representation of Exchange accounts.

    The :meth:`send` method will send all the messages so created and the
    :meth:`verify_receive` will look for the sent messages in the receiving
    ``inbox``.
    """

    def __init__(
            self, accounts=None, logger=None, console_logger=None, **config):
        """
        :arg list accounts: a list of :class:`exchangelib.Account` objects
            If accounts is ``None``, the constructor will build one using
            the data in the ``config`` argument(s)

        :arg logger:

            logging facility; Usually provided by the caller the logger
            data is provided by the calling function but this function is
            capable of creating a :class:`_Logger` instance if needed

        :type logger: :class:`_Logger`

        :arg queue.Queue console_logger:

            the queue used to pass messages to a GUI interface running on the
            main thread

        :arg dict config:

            a :class:`dictionary <dict>` that matches the structure described
            in :ref:`borg_client_config`

            As used in the :ref:`Mail Borg Client Application`, the ``config``
            argument is provided from a :mod:`mail_borg.mail_borg_gui`
            instance.

            It is acceptable to use a ``config`` value generated separately
            as long as it uses the structure referenced above.

            If this argument is not provided, the constructor will invoke the
            :func:`mail_borg.configuration.load_config` function.

        """
        self._sent = False
        """state variable for the send op"""

        self._abort = False
        """
        state variable for an abort

        Aborting happens if there are no messages in the sending queue
        """

        if not config:
            config = load_config()

        self.config = config
        """
        attribute storing all the data required to create an instance
        """

        self.config['wm_id'] = '{}+{}+{}'.format(
            self.config.get('site').get('site', 'no_site'),
            socket.gethostname(),
            datetime.now(tz=get_localzone())
        )

        self.messages = []
        """the `list` of messages that are part of the Exchange check op"""

        self.update_window_queue = console_logger
        """
        store the `queue.Queue` instance used to talk to the outside world
        """

        self.logger = _Logger(
            update_window_queue=console_logger, event_logger=logger)
        """logging attribute"""

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
        """
        the `list` of `exchangelib.Account` instances
        """

        if not self.accounts:
            # stop wasting time
            self._abort = True
            return

        self.witness_emails = []
        """
        the witness emails used in this instance

        See :class:`mail_collector.models.WitnessEmail` for an explanation.
        """
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

        The message subject will end up with a prefix of
        ``[tags][site][hostname]email_subject``
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
        log it, drop it from the list of messages in the instance, and keep
        sending the rest of the messages
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

    # pylint: disable=too-many-branches
    def verify_receive(self, min_wait_receive=None, step_wait_receive=None,
                       max_wait_receive=None):
        """
        look for all the messages that were sent in the receiving ``inbox``

        * for each account:

          * open the account.inbox and search for each message by uuid

            * if found log the sent_at, received_at for further analysis

            * if not found log an error:
              cannot communicate from ``message.account.smtp_address``
              to ``account.inbox.smtp_adddress``

        :arg int wait_receive: minimum delay for searching the ``inboxx``
            measured in seconds seconds

            If ``None``, pick the value from the :attr:`config`

        :arg int step_wait_receive: back-off factor

            If ``None``, pick the value from the :attr:`config`

        :arg int max_wait_receive: maximum delay for searching the ``inbox``

            If ``None``, pick the value from the :attr:`config`

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
            """
            look for the message in the destination inbox

            In case of failure, retry if the failure was one of
            :exc:`exchangelib.ErrorMessageNotFound` or
            :exc:`exchangelib.ErrorTooManyObjectsOpened`. The latter is
            typical of cases when the Exchange server is throttling
            connections.

            The retry operation follows the pattern below:

            * apply the minimal delay

            * try; if it worked, return

            * multiply the current delay by the back-off factor

            * wait for the current delay and try

            * if the current delay has reached the maximum delay, give up
            """
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

    # pylint: enable=too-many-branches
