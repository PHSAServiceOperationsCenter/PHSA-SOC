"""
.. _logger:

:module:    mail_borg.event_logger

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

Logging module for the :ref:`Mail Borg Client Application`

This module is providing facilities for creating Windows event log entries

.. todo::

    Must rename this module to something that suggests its strict
    dependencies to the Windows platform

.. todo::

    Sooner or later we need to make this thing portable

"""
import win32api
import win32con
import win32evtlog
import win32evtlogutil
import win32security

from config import WIN_EVT_CFG


class LogWinEvent():
    '''
    Class wrapper for win32 calls related to writing events to
    the windows logs

    The Python package providing win32 calls is available from
    `pywin32 <https://github.com/mhammond/pywin32>`_. There is very little
    recent documentation.
    The easiest way to figure out how to use this package is to dig through
    the win32/Demos directory and read the sources provided under that
    location.

    For a primer on preparing message resource DLL's, see
    `EventSourceCreationData.MessageResourceFile Property
    <https://docs.microsoft.com/en-us/dotnet/api/system.diagnostics.eventsourcecreationdata.messageresourcefile?view=netframework-4.8>`_.
    Fortunately, the ``pywin32`` comes with a generic message resources DLL
    that will be installed and registered with Windows if the installation
    instructions are followed.
    This class is using this generic message resources DLL
    (actually a .pyd file)  by default.

    The workflow for writing to the Windows events log:

    * create the Windows registry key for this particular combination of
      log type and application unless it already exists

    * if the registry key above has just been created, register the
      the DLL that contains resources associated with these events

    * use any one logging style methods to write events to the Windows log

    '''

    def __init__(self, app_name=None, log_type=None):
        '''
        :arg str app_name:

            the application name as it will appear in the Windows events log

            Will default to 'BorgExchangeMonitor`

        :arg str log_type:

            the Windows events log to write to

            Will default to 'Application'
        '''
        if app_name is None:
            app_name = WIN_EVT_CFG.get('app_name', 'BorgExchangeMon')

        if log_type is None:
            log_type = WIN_EVT_CFG.get('log_type', 'Application')

        self.app_name = app_name
        """
        Instance attribute for the application property of the Windows event

        it is populated in the class constructor
        """
        self.log_type = log_type
        """
        Instance attribute for the log type property of the Windows event
   
        it is populated in the class constructor
        """
        self.sid = None
        """
        Instance attribute for the security identifier (SID) token required
        for accessing the Windows events log

        it is populated via the :meth:`get_sid` method
        """

        if not self.is_registered():
            self.register()

        self.get_sid()

    def get_sid(self):
        """
        get the security identifier require to write to the Windows events log
        """
        token_handle = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_READ)

        self.sid = win32security.GetTokenInformation(
            token_handle, win32security.TokenUser)[0]

    def is_registered(self):
        """
        is there an event source already registered for this application?

        :returns: ``True``or ``False``
        :rtype: bool
        """
        try:
            win32api.RegOpenKey(
                win32con.HKEY_LOCAL_MACHINE,
                '{}\\{}\\{}'.format(WIN_EVT_CFG.get('evt_log_key'),
                                    self.log_type, self.app_name))
            return True
        except:  # @IgnorePep8 pylint: disable=bare-except
            return False

    def register(self, msg_dll=WIN_EVT_CFG.get('msg_dll')):
        """
        register the event source in the windows registry

        This will create the registry needed for creating events for
        this particular combination of log type and application
        """
        win32evtlogutil.AddSourceToRegistry(
            self.app_name, msgDLL=msg_dll, eventLogType=self.log_type)

    def info(self, strings, event_id=7):
        """
        write an INFO level event to the windows events log

        :arg list strings: a list of strings to write to the event

        :arg int event_id:

            the resource identifier for this event

            The event_id values must exist in the messages resource DLL.
            Use this argument only if you really know what you are doing.

        """
        self.msg(event_id=event_id,
                 event_type=win32evtlog.EVENTLOG_INFORMATION_TYPE,
                 strings=strings)

    def warn(self, strings, event_id=8):
        """
        write an WARN level event to the windows events log

        :arg list strings: a list of strings to write to the event

        :arg int event_id:

            the resource identifier for this event

            The event_id values must exist in the messages resource DLL.
            Use this argument only if you really know what you are doing.


        """
        self.msg(event_id=event_id,
                 event_type=win32evtlog.EVENTLOG_WARNING_TYPE,
                 strings=strings)

    def err(self, strings, event_id=9):
        """
        write an ERROR level event to the windows events log

        :arg list strings: a list of strings to write to the event

        :arg int event_id:

            the resource identifier for this event

            The event_id values must exist in the messages resource DLL.
            Use this argunment only if you really know what you are doing.


        """
        self.msg(event_id=event_id,
                 event_type=win32evtlog.EVENTLOG_ERROR_TYPE,
                 strings=strings)

    def msg(self,  event_id, event_type, strings, data=None):
        """
        write an event to windows events log

        :arg event_type: the event type

            it must one of the ``EVENTLOG_FOO_TYPE`` constants defined
            in ``win32evtlog``

        :arg list strings: a list of strings to write to the event

        :arg int event_id: the resource identifier for this event

        :arg bytes data: binary data to write to the event

        """
        win32evtlogutil.ReportEvent(
            self.app_name, event_id, eventType=event_type,
            strings=strings, data=data, sid=self.sid)
