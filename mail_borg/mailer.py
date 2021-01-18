"""
mail_borg.mailer
----------------

This module provides a specialize email only client library for accessing an
`Exchange Web Services (EWS)
<https://searchwindowsserver.techtarget.com/definition/Exchange-Web-Services-EWS>`_
end point.

Email functionality is evaluated using the following concepts:

* ``connect`` to an Exchange server over EWS

* ``send`` an email via an Exchange server over EWS

* ``receive`` the email via an Exchange server over EWS

The ``send`` and ``receive`` terms are somewhat misleading. A ``send`` is
better described as *we are creating an artifact that looks like an email
message on an Exchange server*. A ``receive`` is more or less the equivalent
of *we are accessing an artifact that looks like an email message on an
Exchange server*.

Most members of this module make use of an attribute named
``config``. This attribute is the Python representation of the structure
described in the :ref:`borg_client_config`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca


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
    Credentials, Message, Account, Configuration, DELEGATE, FaultTolerance,
)
from exchangelib.errors import ErrorTooManyObjectsOpened
from retry import retry

from config import load_config
from logger import LogWinEvent


class _Logger:
    """
    Custom logging class that will write to the windows event log, and to
    a GUI window text control if access to one such destination is provided

    When working with GUI applications, the :mod:`mail_borg.mailer` modules
    needs to run on a thread separate from the one where the GUI application
    is running. Communication between these threads is provided via a
    :class:`queue.Queue` instance.

    The methods in this class that take a ``strings`` argument expect that
    said argument can be serialized to ``JSON``.
    The reason for this requirement is architectural in nature; somewhere down
    the line these messages will be put on a wire and the end points expect to
    receive ``JSON`` objects.

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
    executed on the server side.

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


def validate_email_to_ascii(email_address, **config):
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

    :returns:

        a valid, normalized email address value or ``None`` if the
        validation fails. see the :raises: section for a discussion about this

    :raises:

        This function doesn't raise any exceptions because it does its own
        error handling. It is catching and logging:

        :exc:`email_validator.EmailSyntaxError`

        :exc:`email_validator.EmailUndeliverableError`

    """
    if not config:
        config = load_config()

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
        _Logger().warn(
            dict(type='configuration', status='FAIL',
                 wm_id=config.get('wm_id'),
                 account=email_address,
                 message='bad email address %s' % email_address,
                 exception=str(error))
        )
        return None

    if config.get('force_ascii_email'):
        return email_dict.ascii_email

    return email_dict.email


WitnessMessage = collections.namedtuple(
    'WitnessMessage', ['message_uuid', 'message', 'account_for_message'])
"""
class describing an exchange message created using the
:func:`collections.namedtuple` factory function

"""


class WitnessMessages:  # pylint: disable=too-many-instance-attributes
    """
    Class that encapsulates all the functionality required to execute
    an Exchange verification operation once

    An Exchange verification operation consists of sending a message to 
    each Exchange account listed in the ``config`` attribute.
    The verification itself has three components that must all be successful

    * connecting successfully to the Exchange server

    * sending the message successfully

    * finding the sent message in the receiving ``inbox`` successfully


    The main attribute in this class is the Exchange message.
    Each Exchange message contains an ``uuid`` instance generated
    via the :meth:`uuid.uuid4` method in the subject line.
    This way we can search the receiving ``inbox`` for each send message.
    The identifier must be part of the message subject because
    there is a problem with fuzzy searching in the message body on the EWS
    side.
    The class constructor is responsible for creating this identifier.

    Each instance of this class will also create an unique instance identifier.
    This identifier is appended to both the email message itself and,
    more importantly, to the Windows log events created while said class
    instance is active.
    This identifier is used to figure out the site and the bot where
    the log event was collected and the time when when the event was created.
    This identifier is created in the constructor and will become part of
    the :class:`dictionary <dict>` stored in the :attr:`config` instance
    attribute with a key of ``wm_id``.
    The format of this identifier is ``$site+$host+local_timestamp`` where
    ``$site`` is the :class:`mail_collector.models.MailSite` site where the
    client is running and ``$host`` is the name of the bot as returned by the
    :meth:`socket.gethostname` method.

    This class builds a single `exchangelib.Message` with each Exchange
    account defined in the ``config`` argument as recipients. 
    See :func:`get_accounts` for details about the representation of 
    Exchange accounts.

    The :meth:`send` method will send the message so created and the
    :meth:`verify_receive` will look for a forwarded copy of the message
    in the receiving ``inbox`` for each address.
    """

    def __init__(
            self, accounts=None, logger=None, console_logger=None, **config):
        """
        :arg list accounts: a list of :class:`exchangelib.Account` objects
            If accounts is ``None``, the constructor will build one using
            the data in the ``config`` argument(s)

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

        self.message = None
        """the message that are is part of the Exchange check op"""

        self.update_window_queue = console_logger
        """
        store the `queue.Queue` instance used to talk to the outside world
        """

        self.logger = _Logger(
            update_window_queue=console_logger, event_logger=logger)
        """logging attribute"""

        if accounts is None:
            accounts = self.get_accounts()

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

        self.sender = self.parse_account_config(config.get('exchange_client_config').\
                                                        get('sender_account'))
        self.receiver =self.parse_account_config(config.get('exchange_client_config').\
                                                        get('receiver_account'))                                            

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

        
        message_uuid = str(uuid4())
        message_body = 'message_group_id: {}, message_id: {}'.\
            format(self.config.get('wm_id'), message_uuid)
        message = Message(
                    account=self.sender,
                    subject='{} {}'.format(
                        self._set_subject(), message_body),
                    body=message_body,
                    to_recipients=[
                        account.primary_smtp_address
                        for account in self.accounts],
                    cc_recipients=self.witness_emails)
        self.message = WitnessMessage(message_uuid=message_uuid,
                                      message=message,
                                      account_for_message=self.sender)
            

    def get_accounts(self):
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
                        "domain":"PHSABC",fre
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
        exchange_accounts = self.config.get('exchange_client_config').\
            get('exchange_accounts')
            
        accounts = [self.parse_account_config(account) for account in exchange_accounts]  

        if not accounts:
            logger.err(
                dict(type='configuration', status='FAIL',
                     wm_id=self.config.get('wm_id'),
                     account=None,
                     message=(
                         'no valid exchange account found in config for bot %s'
                         % self.config.get('host_name')))
            )
            return None

        return accounts

    def parse_account_config(self, account_defn):
        """
        Produce an `exchangelib.Account` object from our configuration
        
        :arg dict account_defn: 
            A dictionary which contains a definition of a 
            smtp account, which includes an smtp_address string,
            domain_account dictionary, exchange_autodiscover boolean, 
            autodiscover_server string (if autodiscover is false).
            
        :returns:
            The `exchangelib.Account` described by the input, or None
            if the input is malformed.
        """
        if not validate_email_to_ascii(
                    account_defn.get('smtp_address')):
                return

        credentials = Credentials(
            username='{}\\{}'.format(
                account_defn.get('domain_account').get('domain'),
                account_defn.get('domain_account').get('username')),
            password=account_defn.get('domain_account').get('password')
        )

        try:

            if account_defn.get('exchange_autodiscover', True):
                exc_config = Configuration(
                    credentials=credentials, retry_policy=FaultTolerance()
                )

                account = Account(
                    primary_smtp_address=account_defn.get('smtp_address'),
                    config=exc_config, autodiscover=True, access_type=DELEGATE
                )

            else:
                exc_config = Configuration(
                    server=account_defn.get('autodiscover_server'),
                    credentials=credentials, retry_policy=FaultTolerance()
                )

                account = Account(
                    primary_smtp_address=account_defn.get('smtp_address'),
                    config=exc_config, autodiscover=False,
                    access_type=DELEGATE
                )

            self.logger.info(
                dict(type='connection', status='PASS',
                     wm_id=self.config.get('wm_id'),
                     message='connected to exchange',
                     account='{}\\{}, {}'.format(
                         account_defn.get('domain_account').get('domain'),
                         account_defn.get(
                             'domain_account').get('username'),
                         account_defn.get('smtp_address')))
            )

        except Exception as error:
            self.logger.err(
                dict(type='connection', status='FAIL',
                     wm_id=self.config.get('wm_id'),
                     message='cannot connect to exchange',
                     account='{}\\{}, {}'.format(
                         account_defn.get('domain_account').get('domain'),
                         account_defn.get(
                             'domain_account').get('username'),
                         account_defn.get('smtp_address')),
                     exeption=str(error))
            )
            return
        
        return account

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

    def send(self, min_wait_receive=None, step_wait_receive=None,
             max_wait_receive=None):
        """
        Send the message as constructed in the constructor.
        
        If sending raises an error log it.

        This method uses a pattern known as `retry with exponential back-off
        and circuit breaker
        <https://dzone.com/articles/understanding-retry-pattern-with-exponential-back>`__
        to control connections to the `EWS
        <https://docs.microsoft.com/en-us/exchange/client-developer/exchange-web-services/start-using-web-services-in-exchange>`__
        server.

        :arg int wait_receive: minimum wait when retrying an Exchange action;
            in this case, this is the minimum retry wait for resending the
            Exchange message measured in seconds

            If `None`, pick the value from the :attr:`config` attribute.

        :arg int step_wait_receive: back-off factor for retrying an Exchange
            action

            If `None`, pick the value from the :attr:`config` attribute.

        :arg int max_wait_receive: maximum time to wait before giving up
            on an Exchange action

            If `None`, pick the value from the :attr:`config` attribute.


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

        @retry((ErrorTooManyObjectsOpened,), delay=int(min_wait_receive),
               max_delay=int(max_wait_receive), backoff=int(step_wait_receive))
        def send_message(message):
            """
            send the Exchange message using the `retry with exponential
            back-off and circuit breaker` pattern`

            The typical exception that triggers the retry is when the
            `EWS ResponseMessage
            <https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/responsemessage>`__
            contains an `ErrorTooManyObjectsOpened` error.
            """
            message.message.send()

        if self._abort:
            if self.update_window_queue:
                self.update_window_queue.put_nowait(('abort',))

            return 'mail check abort'

        if not self.message:
            self.logger.err(
                dict(type='create', status='FAIL',
                     wm_id=self.config.get('wm_id'),
                     account=None,
                     message=(
                         'could not create any messages with the'
                         ' config of bot %s' % self.config.get('host_name')))
            )
            return 'nothing to send'
        
        msg_dict = dict(type='send', status='PASS',
                     wm_id=self.config.get('wm_id'),
                     account=self.message.account_for_message.
                     primary_smtp_address,
                     message='monitoring message sent',
                     message_uuid=str(self.message.message_uuid),
                     from_email=self.message.
                     account_for_message.primary_smtp_address,
                     to_emails=', '.join([email for email in
                                          self.message.message.to_recipients]))
        try:
            send_message(self.message)

            self.logger.info(msg_dict)

        except Exception as error:
            msg_dict['status']='FAIL'
            msg_dict['exception']=str(error)
            msg_dict['message']='monitoring message failure'
            self.logger.err(msg_dict)

            raise error

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
              to ``account.inbox.smtp_address``

        This method uses a pattern known as `retry with exponential back-off
        and circuit breaker
        <https://dzone.com/articles/understanding-retry-pattern-with-exponential-back>`__
        to control connections to the `EWS
        <https://docs.microsoft.com/en-us/exchange/client-developer/exchange-web-services/start-using-web-services-in-exchange>`__
        server.

        :arg int wait_receive: minimum wait when retrying an Exchange action;
            in this case, this is the minimum retry wait for searching the
            Exchange account `inbox` measured in seconds

            If `None`, pick the value from the :attr:`config` attribute.

        :arg int step_wait_receive: back-off factor for retrying an Exchange
            action

            If `None`, pick the value from the :attr:`config` attribute.

        :arg int max_wait_receive: maximum time to wait before giving up
            on an Exchange action

            If `None`, pick the value from the :attr:`config` attribute.

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

        self.send()

        time.sleep(min_wait_receive)

        #TODO clean up this logging.
        msg_dict = dict(type='receive', status='FAIL',
                     wm_id=self.config.get('wm_id'),
                     account=self.message.account_for_message.
                     primary_smtp_address,
                     message_uuid=str(self.message.message_uuid),
                     from_email = self.message.account_for_message.primary_smtp_address,
                     to_emails=', '.join(
                         [r.email_address for r in
                          self.message.message.to_recipients]))

        #make a copy of self.accounts so we can delete accounts as we receive the message from them.
        self.unseen_recipients = [r for r in self.accounts] 

        @retry((ErrorTooManyObjectsOpened, ErrorMessageNotFound),
           delay=int(min_wait_receive), max_delay=int(max_wait_receive),
           backoff=int(step_wait_receive))
        def check_inbox():
            msgs = self.receiver.inbox.filter(subject__icontains=str(self.message.message_uuid))
            
            to_remove = [account for account in self.unseen_recipients 
                         if account.primary_smtp_address 
                         in [msg.sender.email_address for msg in msgs]]
            
            for msg in msgs.all():
                msg_dict['to_emails'] = [msg.sender.email_address]  # the msg was sent to this address before being forwarded back.
                msg_dict['to_addresses'] = [msg.sender.email_address]
                msg_dict['from_address'] = msg.author.email_address
                msg_dict['status'] = 'PASS'
                msg_dict['message'] = 'message recieved'
                msg_dict['created'] = str(msg.datetime_created)
                msg_dict['sent'] = str(msg.datetime_sent)
                msg_dict['received'] = str(msg.datetime_received)
                
                self.logger.info(msg_dict)
            
            self.unseen_recipients = [r for r in self.unseen_recipients if r not in to_remove]

            if self.unseen_recipients:
                raise ErrorMessageNotFound #force retry if we haven't see the message delivered to each mailbox)
                
        check_inbox()
        
        for r in self.unseen_recipients:
            msg_dict['to_emails'] = [r]  # the msg was sent to this address before being forwarded back.
            msg_dict['from_address'] = None
            msg_dict['status'] = 'FAIL'
            msg_dict['message'] = 'message not seen'
            msg_dict['created'] = None
            msg_dict['sent'] = None
            msg_dict['received'] = None
            
            self.logger.err(msg_dict)
            
        self.unseen_recipients = None

        if self.update_window_queue:
            self.update_window_queue.put_nowait(('control',))

    # pylint: enable=too-many-branches
