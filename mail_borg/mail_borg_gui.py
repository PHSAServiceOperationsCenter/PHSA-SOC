"""
.. _mail_borg_gui:

:module:    mail_borg.mail_borg_gui

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

GUI module for the :ref:`Mail Borg Client Application`

This module is built using the `PySimpleGUI
<https://pysimplegui.readthedocs.io/en/latest/>`_ package.

:note:

    GUI interfaces creating using the `PySimpleGUI
    <https://pysimplegui.readthedocs.io/en/latest/>`_ package cannot be
    resized.
    This application is optimized for screens running at a resolution of
    1920 x 1080 pixels.

"""
import collections
from datetime import datetime, timedelta
from queue import Queue
import sys
import threading
import time

import PySimpleGUI as Gui
from config import ConfigManager, HTTP_PROTO, WIN_EVT_CFG
from mailer import WitnessMessages


class WindowManager:
    def __init__(self):
        self.window = None
        # TODO merge config and base configs?
        self.config_mgr = ConfigManager()
        self.config_is_dirty = False
        self.new_window()

        Gui.SetOptions(font='Any 10', button_color=('black', 'lightgrey'))

        self.update_queue = Queue(maxsize=500)
        self._accounts_to_table(
            self.get_config_val('exchange_client_config', {})
                .get('exchange_accounts', []))

        self._next_run_at = datetime.now() + timedelta(
            minutes=int(self._get_element('mail_check_period')))
        self._set_autorun()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, tb):
        self.window.Close()

    def _accounts_to_table(self, accounts):
        """
        Information pertinent to Exchange accounts is displayed using a
        `PySimpleGUI.Table` element.

        This function is reponsible for taking a list of Exchange accounts and
        generating a `PySimpleGUI.Table` row for each account.

        An Exchange account is described by the structure shown below:

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

        """
        account_pairs = [(account, account.get('domain_account'))
                         for account in accounts]

        listed_accounts = \
            [
                [domain_account.get('domain'),
                 domain_account.get('username'),
                 domain_account.get('password'),
                 account.get('smtp_address'),
                 account.get('exchange_autodiscover'),
                 account.get('autodiscover_server')]
                for account, domain_account in account_pairs
            ]

        self._update_element('exc_accs', listed_accounts)

    def _dirty_window(self):
        """
        update various ``GUI`` elements to reflect the
        :attr:`main.config_is_dirty` state variable
        """
        self._update_element('save_config', disabled=False)
        self._update_element('reset_config', disabled=False)

    def _get_element(self, elem_name):
        return self.window.FindElement(elem_name).Get()

    def _mail_check(self):
        """
        the threaded call to the :class:`mail_borg.mailer.WitnessMessages`
        instance used to execute the Exchange verification op

        :arg `PySimpleGUI.window` window: the window object associated with the
            ``GUI`` interface. This argument is used to update various elements
            in the ``GUI``. This includes updating the `PySimpleGUI.Text`
            element that shows the status of the application and disabling and/or
            enabling various `PySimpleGUI.Button` elements

        :arg `queue.Queue` update_window_queue: the `queue.Queue` used to pass
            information between the Exchange verification thread and the ``GUI``
            (main) thread

        """
        try:
            witness_messages = WitnessMessages(
                console_logger=self.update_queue, **self.config_mgr.config)
        except AttributeError:
            # TODO what is causing this?
            print('Yup we caught it.')
        else:
            witness_messages.verify_receive()

    def _pause(self):
        """
        update various ``GUI`` elements to reflect the :attr:`main.autorun` state
        variable
        """
        self._update_element('status',
                             'automated mail check execution is paused')
        self.set_pause(True)

    # TODO what is this for?
    def _set_autorun(self):
        """
        calculate the value of the :attr:`main.autorun` state variable
        """
        if self._get_element('autorun'):
            self.set_pause(False)
        else:
            self._pause()

    def _set_pause(self, pause):
        self._update_element('pause', disabled=pause)
        self._update_element('run', disabled=not pause)

    def _update_next_run_in(self):
        """
        update the time counter for the next :func:`mail_check` call

        :arg `datetime.datetime` next_run_at: the moment for the next
            :func:`mail_check` call

            This moment is re-evaluated every time the :func:`mail_check` is called
            and it is stored in a state variable in the :func:`main` function.

        :returns: a :class:`tuple` in minutes, seconds format that represents the
            time left until the next call of the :func:`mail_check`
        """
        mins, secs = divmod((self.next_run_at - datetime.now()).total_seconds(), 60)
        self._update_element('status', f'next mail check run in '
                                       f'{mins} minutes, {secs} seconds')

    def _witness_emails_from_list(self, witness_emails):
        """
        populate the ``GUI`` element used for showing
        :class:`mail_collector.models.WitnessEmail` instances used in the
        main configuration

        This ``GUI`` element is accepting only :class:`str` data while the
        :class:`mail_collector.models.WitnessEmail` data is provided as a
        :class:`list`.

        """
        self._update_element('witness_addresses', ', '.join(witness_emails))

    def _update_element(self, elem_name, *args, **kwargs):
        return self.window.FindElement(elem_name).Upadate(*args, **kwargs)

    def _update_output(self, msg, **kwargs):
        out_elem = self.FindElement('output')
        out_elem.Update(disabled=False)
        out_elem.Update(msg, **kwargs)
        out_elem.Update(disabled=True)

    def get_config_val(self, elem_name, default=None):
        return self.config_mgr.config.get(elem_name, default)

    def mail_check(self):
        """
        start the `threading.Thread` where the Exchange verification op is
        executed

        This function is called from the OnClickUp event of the
        ``Run Mail Check Now`` `PySimpleGUI.Button`.

        :arg dict config: the main configuration that is currently active. Note
            that this :ref:`configuration <borg_client_config>` may have been
            changed locally in the ``GUI`` interface

        :arg `PySimpleGUI.window` window: the window object associated with the
            ``GUI`` interface. This argument is used to update various elements
            in the ``GUI``. This includes updating the `PySimpleGUI.Text`
            element that shows the status of the application and disabling and/or
            enabling various `PySimpleGUI.Button` elements

        :arg `queue.Queue` update_window_queue: the `queue.Queue` used to pass
            information between the Exchange verification thread and the ``GUI``
            (main) thread

        """
        self._update_element('mailcheck', disabled=True)
        if not self.window.FindElement('run').Disabled:
            self._update_element('run', disabled=True)
        if not self.window.FindElement('pause').Disabled:
            self._update_element('pause', disabled=True)
        self._update_element('status', 'running mail check')
        self._update_output(
            '{:%c}: running mail check\n'.format(datetime.now()), append=True)

        thr = threading.Thread(target=self._mail_check, args=(
            self.update_queue, dict(self.config_mgr.config)))
        thr.start()

    def new_window(self):
        """
        Function that builds the GUI interface and all its elements

        :returns:

            a :class:`tuple` containing

            * the ``basic configuration`` as loaded into the ``GUI`` on launch
            * the ``main configuration`` as loaded into the ``GUI`` on launch
            * the `PySimpleGUI.window` object of the
              :ref:`Mail Borg Client Application`

        GUI elements showing main configuration data are populated using
        the :func:`mail_borg.config.load_config` function.

        GUI elements showing basic configuration data are populated using the
        :func:`mail_borg.config.load_base_configuration` function.
        """
        self.window = Gui.Window(WIN_EVT_CFG['app_name'],
                                 auto_size_buttons=True,
                                 use_default_focus=False)

        control_frame = [
            [Gui.Text('',  key='status', size=(133, 1),  justification='left'),
             Gui.Button('Run Mail Check Now', key='mailcheck'),
                Gui.Button('Start Auto-run', key='run'),
                Gui.Button('Pause Auto-run', key='pause'), ],
        ]

        output_frame = [
            [Gui.Multiline(size=(200, 10), key='output', disabled=True,
                           autoscroll=True, enable_events=True), ],
            [Gui.Text('', size=(161, 1)),
             Gui.Button('Clear execution data', key='clear'), ]
        ]

        # Default to an empty dict to avoid AttributeErrors from calling get on
        # a None object
        exch_client_conf = self.get_config_val('exchange_client_config', {})

        conf_labels_col = [
            [Gui.Checkbox(
                'Enable Auto-run on startup', key='autorun', enable_events=True,
                default=exch_client_conf.get('autorun', False)), ],
            [
                Gui.Checkbox(
                    'Debug', default=exch_client_conf.get('debug', False),
                    key='debug', enable_events=True),
                Gui.Checkbox(
                    'Verify MX deliverability',
                    default=exch_client_conf.get('check_mx', False),
                    key='check_mx', enable_events=True),
            ],
            [Gui.Text('Verify MX Timeout:', justification='left'), ],
            [Gui.Text(
                'Min. wait to retry Exchange action:',
                justification='left'), ],
            [Gui.Text(
                'Back-off retry factor for Exchange action:',
                justification='left'), ],
            [Gui.Text(
                'Max. time to retry an Exchange action:',
                justification='left'), ],
            [Gui.Text('Originating Site:', justification='left'), ],
            [Gui.Text('Mail Subject:', size=(None, 1), justification='left'), ],
            [Gui.Multiline(exch_client_conf.get('email_subject', ''),
                           key='email_subject', size=(32, 3),
                           auto_size_text=True, do_not_clear=True,
                           enable_events=True), ],
        ]

        conf_values_col = [
            [Gui.Text('Check Email Every', justification='left'),
             # TODO do spinners actually require lists? (probably yes...)
             Gui.Spin(
                list(range(1, 60)), key='mail_check_period',
                initial_value=exch_client_conf.get('mail_check_period', 60),
                size=(3, 1), enable_events=True),
             Gui.Text('minutes'), ],
            [Gui.Checkbox(
                'Force ASCII email',
                default=exch_client_conf.get('ascii_address', False),
                key='ascii_address',  enable_events=True),
             Gui.Checkbox(
                 'UTF-8 addresses',
                default=exch_client_conf.get('utf8_email', False),
                key='utf8_email', enable_events=True), ],
            [Gui.Spin(
                list(range(1, 20)),
                key='check_mx_timeout',
                initial_value=exch_client_conf.get('check_mx_timeout', 20),
                size=(3, 1), enable_events=True),
             Gui.Text('seconds'), ],
            [Gui.Spin(
                list(range(1, 120)), key='min_wait_receive',
                initial_value=exch_client_conf.get('min_wait_receive', 120),
                size=(3, 1), enable_events=True),
             Gui.Text('seconds'), ],
            [Gui.Spin(
                list(range(1, 10)), key='backoff_factor',
                initial_value=exch_client_conf.get('backoff_factor', 10),
                size=(3, 1), enable_events=True), ],
            [Gui.Spin(
                list(range(1, 600)), key='max_wait_receive',
                initial_value=exch_client_conf.get('max_wait_receive', 600),
                size=(3, 1),  enable_events=True),
             Gui.Text('seconds'), ],
            [Gui.InputText(self.get_config_val('site', {}).get('site', ''),
                           key='site', size=(32, 1), disabled=True), ],
            [Gui.Text('Additional Email Tags:',
                      size=(None, 1), justification='left'), ],
            [Gui.Multiline(exch_client_conf.get('tags', ''), key='tags',
                           size=(32, 3), auto_size_text=True, do_not_clear=True,
                           enable_events=True), ], ]

        conf_emails_col = [
            [Gui.Text('Exchange Accounts:',  justification='left'), ],
            [Gui.Table(
                [[None, None, None, None, None, None]],
                headings=['domain', 'username', 'password', 'smtp',
                          'autodiscover', 'autodiscover server'], key='exc_accs',
                auto_size_columns=True, display_row_numbers=True), ],
            [Gui.Text('Witness Addresses:', justification='left'), ],
            [Gui.Multiline(
                ', '.join(exch_client_conf.get('witness_addresses', [])),
                size=(96, 1), key='witness_addresses', disabled=True), ], ]

        config_frame = [
            [Gui.Checkbox('Load Config from Server',
                          default=self.base_config.get('use_cfg_srv'),
                          key='use_cfg_srv', enable_events=True),
             Gui.Text('Config Server Address', justification='left'),
             Gui.InputText(self.base_config.get('cfg_srv_ip'), key='cfg_srv_ip',
                           size=(12, 1), do_not_clear=True, enable_events=True),
             Gui.Text('Config Server Port', justification='left'),
             Gui.InputText(self.base_config.get('cfg_srv_port'), key='cfg_srv_port',
                           size=(5, 1), do_not_clear=True, enable_events=True),
             Gui.Text('Connection timeout'),
             Gui.InputText(self.base_config.get('cfg_srv_conn_timeout'),
                           key='cfg_srv_conn_timeout', size=(3, 1),
                           do_not_clear=True, enable_events=True),
             Gui.Text('Read timeout'),
             Gui.InputText(self.base_config.get('cfg_srv_read_timeout'),
                           key='cfg_srv_read_timeout', size=(3, 1),
                           do_not_clear=True, enable_events=True),
             Gui.Text('', size=(39, 1)),
             Gui.Button('Save local config', key='save_config',
                        disabled=True),
             Gui.Button('Reset local config', key='reset_config',
                        disabled=False), ],
            [Gui.Text(self.config.get('load_status',
                                      'Configuration did not load correctly.'))
             ],
        ]

        mail_check_frame = [
            [
                Gui.Text(
                    ('Configuration changes are not preserved across startups.'
                     ' To persist changes, edit the configuration on the server at')),
                Gui.InputText(
                    '{}://{}:{}/admin/mail_collector/exchangeconfiguration/?q={}'.
                    format(
                        HTTP_PROTO, self.base_config.get('cfg_srv_ip'),
                        self.base_config.get('cfg_srv_port'),
                        exch_client_conf.get('config_name',
                                             'ERROR: CONFIG NOT LOADED')),
                    disabled=True, size=(80, 1), key='bot_cfg_url'),
                Gui.Button('Refresh config from server', key='reload_config',
                           disabled=False),
            ],
            [
                Gui.Column(conf_labels_col),
                Gui.Column(conf_values_col),
                Gui.Column(conf_emails_col),
            ],
        ]

        layout = [
            [Gui.Frame('Control',
                       control_frame, title_color='darkblue', font='Any 12'), ],
            [Gui.Frame('Local configuration',
                       config_frame, title_color='darkblue', font='Any 12'), ],
            [Gui.Frame('Exchange verification configuration',
                       mail_check_frame, title_color='darkblue', font='Any 12'),
             ],
            [Gui.Frame('Output',
                       output_frame, title_color='darkblue', font='Any 12'), ]]

        self.window.Layout(layout).Finalize()

    def reload_config(self):
        """
        abandon the main configuration shown in the ``GUI`` interface and
        reload the main configuration from either the ``SOC Automation server``,
        or the locally cached main configuration

        This function is invoked by the OnClickUp event of the ``Refresh config
        from server`` `PySimpleGUI.Button` element.

        The source of the new main configuration is determined based on the state
        of the ``Load Config from Server`` `PySimpleGUI.Checkbox` element.

        The function assembles the current basic configuration from the
        associated ``GUI`` elements and uses it as an argument to the
        :func:`mail_borg.config.load_config` function. It then re-populates
        the main configuration ``GUI`` controls with the new data.

        :arg `PySimpleGUI.window` window: the window objects associated with
            the ``GUI`` interface
        """
        self.config_mgr.clear_conifg()

        self.window.FindElement('bot_cfg_url').Update(
            f'{HTTP_PROTO}://{self.config_mgr.server.ip}:'
            f'{self.config_mgr.server.port}/admin/mail_collector/mailhost/'
            f'?q={self.get_config_val("host_name")}'
        )

        # TODO this is similar to above, is there some way to refactor to reduce
        #      code duplication?
        exch_client_conf = self.get_config_val('exchange_client_config', {})

        update_defaults = {
            'autorun': False,
            'debug': False,
            'check_mx': False,
            'email_subject': '',
            'mail_check_period': 60,
            'ascii_address': False,
            'utf8_email': False,
            'check_mx_timeout': 10,
            'min_wait_receive': 10,
            'backoff_factor': 1,
            'max_wait_receive': 120,
            'tags': []
        }

        for elem in update_defaults:
            self._update_element(elem,
                                 exch_client_conf.get(elem,
                                                      update_defaults[elem]))
        # site is not stored in the exchange client configuration, so we handle
        # it separately
        self._update_element('site', self.config.get('site').get('site'))
        self._accounts_to_table(exch_client_conf.get('exchange_accounts', []))
        self._witness_emails_from_list(
            exch_client_conf.get('witness_addresses', []))

    def reset_config(self):
        """
        reload the basic configuration active in the ``GUI`` with the
        values defined in the :attr:`mail_borg.config.INI_DEFAULTS`

        Note that these defaults, particularly the value of the ``cfg_srv_ip``
        (the address of the ``SOC Automation server``) may be out of date.

        This function is invoked by the OnCLickUp event of the ``Reset local
        config`` `PySimpleGUI.Button` element.
        """
        self.config_mgr = ConfigManager()
        for key, value in self.config_mgr.server_config.items():
            self._update_element(key, value)

    def save_config(self):
        """
        call the :func:`mail_borg.config.save_basic_configuration` to save
        changes made to the local configuration from the ``GUI`` interface

        This function is invoked by OnClickUp event of the ``Save local config``
        `PySimpleGUI.Button`

        :arg `PySimpleGUI.window` window: the window object associated with the
            ``GUI`` interface. This function will access the values of the
            ``GUI`` elements associated with the local configuration and pass
            them to the saving function

        """
        items = [('use_cfg_srv', bool()),
            ('cfg_srv_ip', self._get_element('cfg_srv_ip')),
            ('cfg_srv_port', int(self._get_element('cfg_srv_port'))), (
            'cfg_srv_conn_timeout',
            int(self._get_element('cfg_srv_conn_timeout'))), (
            'cfg_srv_read_timeout',
            int(self._get_element('cfg_srv_read_timeout'))), ]

        self.config_mgr.server_config = collections.Ordereddict(items)

        self.config_mgr.save_server_configuration()

    def tick(self):
        event, values = self.window.Read(timeout=0)

        if values is None or event == 'Exit':
            if self.config_is_dirty:
                save = Gui.PopupYesNo('Save configuration?',
                    'There are unsaved changes'
                    ' in the application configuration.'
                    ' Do you wish to save them?')

                if save == 'Yes':
                    self.save_config(self.config)

            return False

        while not self.update_queue.empty():
            msg = self.update_queue.get_nowait()
            if msg[0] == 'output':
                self._update_output(msg[1], append=True)
                self._update_element('status', 'mail check in progress')

            elif msg[0] == 'abort':
                self._update_output('\nmail check aborted\n', append=True)
                self._update_element('status',
                                     'Mail check aborted. Please verify '
                                     'the configuration is correct.')
                self._update_element('autorun', value=False)

            elif msg[0] == 'control':
                self._update_output('\nmail check complete\n', append=True)
                self._update_element('mail_check_period', disabled=False)
                self._update_element('mailcheck', disabled=False)
                if self._get_element('autorun'):
                    self._update_element('pause', disabled=False)
                    next_run_at = datetime.now() + timedelta(minutes=int(
                        self._get_element('mail_check_period')))
                    self._update_next_run_in()
                else:
                    self._update_element('run', disabled=False)
                    self._update_element(
                        'status', 'Automated mail check execution is paused.')

        if event in ['use_cfg_srv', 'cfg_srv_ip', 'cfg_srv_port',
                     'cfg_srv_conn_timeout', 'cfg_srv_conn_timeout']:
            self.config_is_dirty = True
            self.config_mgr.server_config[event] = \
                self._get_element(event).replace('\n', '')

            self._dirty_window()

            if event == 'autorun':
                self._set_autorun()

            if event == 'mail_check_period':
                next_run_at = datetime.now() + timedelta(
                    minutes=int(self._get_element('mail_check_period')))

        if event == 'save_config':
            self.save_config()
            self._update_element('save_config', disabled=True)
            self.config_is_dirty = False

        if event == 'reset_config':
            self.reset_config()

        if event == 'reload_config':
            self.reload_config()

        if event == 'clear':
            self._update_output('')

        if self._get_element('autorun'):
            self._update_element('pause', disabled=False)
            self._update_element('status',
                                 f'next mail check run in '
                                 f'{self.next_run_in(next_run_at)}')

            if next_run_at <= datetime.now():
                self.mail_check()
                next_run_at = datetime.now() + \
                              timedelta(minutes=int(self._get_element(
                                  'mail_check_period')))

        if event == 'mailcheck':
            self.mail_check()
            self.next_run_at = datetime.now() + \
                          timedelta(
                              minutes=int(
                                  self._get_element('mail_check_period')))

            # TODO how/why is this different from _pause
            if self._get_element('autorun'):
                self._update_element('run', disabled=True)
                self._update_element('pause', disabled=False)
                self._update_element('status',
                                     f'next mail check run in '
                                     f'{self.next_run_in(next_run_at)}')
            else:
                self._update_element('run', disabled=False)
                self._update_element('pause', disabled=True)
                self._update_element('status',
                                     'automated mail check execution is paused')

        if event == 'pause':
            self._update_element('autorun', False)
            self._pause()

        if event == 'run':
            self._update_element('autorun', True)
            self._update_element('run', disabled=True)
            self._update_element('pause', disabled=False)
            self._update_element('status',
                                 f'next mail check run in {self.next_run_at}')

        return True


def main():
    """
    The ``main()`` function

    This is the entry point to the script using this module.

    For a discussion about ``main()`` functions in `Python
    <https://www.python.org/about/>`_, please see
    `Defining Main Functions in Python
    <https://realpython.com/python-main-function/>`_.

    Under normal ops this module is never imported anywhere and using a
    ``main()`` function and the `__main__ Python facility
    <https://docs.python.org/3.6/library/__main__.html?highlight=__main__>`_
    is not needed.

    The requirement for using the ``main()`` function is introduced by our
    choice to use the `Sphinx autodoc extension
    <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
    for generating documentation. This extension needs to import all the
    modules that are self-documented using ``docstrings``. The extension
    will not be able to import this module unless the ``main()`` function
    mechanism is being used

    :state variables:

        :config_is_dirty:

            local state variable keeping track of whether the ``basic
            configuration`` currently shown in the ``GUI`` interface is different
            from the ``basic configuration`` that was initially loaded in the
            ``GUI`` i.e. from a stored medium

            This variable is consulted on ``Exit`` and a ``dialog box``
            prompting the user to save a changed (dirty) ``basic
            configuration`` if the variable is ``True``.

            The variable is set if the value of any `PySimpleGUI.window` element
            matching an entry in the :class:`editable <list>` has changed.

            The variable is reset when the ``Save local config``
            `PySimpleGU.Button` element is clicked.

        :autorun:

            local state variable keeping track of whether the :func:`mail_check`
            function is invoked automatically or manually

        :next_run_at:

            Local `datetime.datetime` variable that keeps track of when the
            :func:`mail_check` will execute next but only if the :attr:`autorun`
            is ``True``

    :control variables:

        :editable:

            local :class:`list` that used for identifying ``GUI`` elements
            that will trigger a state change for the :attr:`config_is_dirty`
            variable

        :update_window_queue:

            `queue.Queue` that is used for keeping track of the state of
            the ``Exchange verification op`` `threading.Thread` launched by
            the :func:`mail_check` function

            The following "events" will be delivered via this `queue.Queue`:

            * ``output``: update the status tracking ``GUI`` elements with
              the progress of the ``Exchange verification op``

            * ``abort``: the ``Exchange verification op`` has been aborted.
              Set various ``GUI`` elements accordingly.

            * ``control``: the ``Exchange verification op`` has completed
               successfully. Make ready for the next ``Exchange verification
               op`` taking into consideration the value of the
               :attr:`autorun` state variable

    """
    with WindowManager() as manager:
        while manager.tick():
            time.sleep(1)


if __name__ == '__main__':
    if sys.platform != 'win32':
        raise OSError('%s will not work on %s' % (__name__, sys.platform))

    main()
