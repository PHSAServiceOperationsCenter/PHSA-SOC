"""
.. _logger:

logger module for exchange monitoring borg bots

will write events to the windows event logs

:module:    mail_borg.event_logger

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    apr. 12, 2019

"""
import win32api
import win32con
import win32evtlog
import win32evtlogutil
import win32security

from config import WIN_EVT_CFG


class LogWinEvent():
    '''
    class to encapsulate win32 calls related to writing events to
    the windows logs
    '''

    def __init__(self, app_name=None, log_type=None):
        '''
        Constructor
        '''
        if app_name is None:
            app_name = WIN_EVT_CFG.get('app_name', 'BorgExchangeMon')

        if log_type is None:
            log_type = WIN_EVT_CFG.get('log_type', 'Application')

        self.app_name = app_name
        self.log_type = log_type
        self.sid = None

        if not self.is_registered():
            self.register()

        self.get_sid()

    def get_sid(self):
        """
        get the security identifier require to write to the events log
        """
        token_handle = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_READ)

        self.sid = win32security.GetTokenInformation(
            token_handle, win32security.TokenUser)[0]

    def is_registered(self):
        """
        is there an event source already registered for this application?
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
        register mthe event source in the windows regisstry
        """
        win32evtlogutil.AddSourceToRegistry(
            self.app_name, msgDLL=msg_dll, eventLogType=self.log_type)

    def info(self, strings, event_id=7):
        """
        write an INFO level event to the windows events log
        """
        self.msg(event_id=event_id,
                 event_type=win32evtlog.EVENTLOG_INFORMATION_TYPE,
                 strings=strings)

    def warn(self, strings, event_id=8):
        """
        write an WARN level event to the windows events log
        """
        self.msg(event_id=event_id,
                 event_type=win32evtlog.EVENTLOG_WARNING_TYPE,
                 strings=strings)

    def err(self, strings, event_id=9):
        """
        write an ERROR level event to the windows events log
        """
        self.msg(event_id=event_id,
                 event_type=win32evtlog.EVENTLOG_ERROR_TYPE,
                 strings=strings)

    def msg(self,  event_id, event_type, strings, data=None):
        """
        write an event to windows events log
        """
        win32evtlogutil.ReportEvent(
            self.app_name, event_id, eventType=event_type,
            strings=strings, data=data, sid=self.sid)
