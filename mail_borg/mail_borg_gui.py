"""
.. _mail_borg_gui:

:module:    mail_borg.mail_borg_gui

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Sep. 20, 2019

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

import PySimpleGUI as gui
from config import (
    load_config, load_base_configuration, WIN_EVT_CFG, HTTP_PROTO,
    save_base_configuration, reset_base_configuration,
)
from mailer import WitnessMessages


gui.SetOptions(font='Any 10', button_color=('black', 'lightgrey'))

# pylint: disable=unnecessary-comprehension
# PySimpleGUI.Spin() likes comprehensions for populating the spinner even if
# pylint disapproves


def get_window():
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
    config = load_config()
    base_config = load_base_configuration()

    window = gui.Window(WIN_EVT_CFG.get('app_name'),
                        auto_size_buttons=True, use_default_focus=False)

    control_frame = [
        [gui.Text('',  key='status', size=(133, 1),  justification='left'),
         gui.Button('Run Mail Check Now', key='mailcheck'),
            gui.Button('Start Auto-run', key='run'),
            gui.Button('Pause Auto-run', key='pause'), ],

    ]

    output_frame = [
        [gui.Multiline(size=(200, 10), key='output', disabled=True,
                       autoscroll=True, enable_events=True), ],
        [gui.Text('', size=(161, 1)),
         gui.Button('Clear execution data', key='clear'), ]
    ]

    conf_labels_col = [
        [gui.Checkbox(
            'Enable Auto-run on startup', key='autorun',  enable_events=True,
            default=config.get('exchange_client_config').get('autorun')), ],
        [
            gui.Checkbox(
                'Debug',
                default=config.get('exchange_client_config').get('debug'),
                key='debug', enable_events=True),
            gui.Checkbox(
                'Verify MX deliverability',
                default=config.get('exchange_client_config').get('check_mx'),
                key='check_mx', enable_events=True),
        ],
        [gui.Text('Verify MX Timeout:', justification='left'), ],
        [gui.Text(
            'Minimum wait when retrying an Exchange action:',
            justification='left'), ],
        [gui.Text(
            'Back-off factor for retrying an Exchange action:',
            justification='left'), ],
        [gui.Text(
            'maximum time to wait before giving up on an Exchange action:',
            justification='left'), ],
        [gui.Text('Originating Site:', justification='left'), ],
        [gui.Text('Mail Subject:', size=(None, 1), justification='left'), ],
        [gui.Multiline(config.get(
            'exchange_client_config').get('email_subject'),
            key='email_subject', size=(32, 3), auto_size_text=True,
            do_not_clear=True,  enable_events=True), ],
    ]

    conf_values_col = [
        [gui.Text('Check Email Every', justification='left'),
         gui.Spin(
            [i for i in range(1, 60)], key='mail_check_period',
            initial_value=config.get(
                'exchange_client_config').get('mail_check_period'),
            size=(3, 1), enable_events=True),
         gui.Text('minutes'), ],
        [gui.Checkbox(
            'Force ASCII email',
            default=config.get('exchange_client_config').get('ascii_address'),
            key='ascii_address',  enable_events=True),
         gui.Checkbox(
             'UTF-8 addresses',
            default=config.get('exchange_client_config').get('utf8_email'),
            key='utf8_email', enable_events=True), ],
        [gui.Spin(
            [i for i in range(1, 20)],
            key='check_mx_timeout',
            initial_value=config.get(
                'exchange_client_config').get('check_mx_timeout'),
            size=(3, 1), enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin(
            [i for i in range(1, 120)], key='min_wait_receive',
            initial_value=config.get(
                'exchange_client_config').get('min_wait_receive'),
            size=(3, 1), enable_events=True),
         gui.Text('seconds'), ],
        [gui.Spin(
            [i for i in range(1, 10)], key='backoff_factor',
            initial_value=config.get(
                'exchange_client_config').get('backoff_factor'),
            size=(3, 1), enable_events=True), ],
        [gui.Spin(
            [i for i in range(1, 600)], key='max_wait_receive',
            initial_value=config.get(
                'exchange_client_config').get('max_wait_receive'),
            size=(3, 1),  enable_events=True),
         gui.Text('seconds'), ],
        [gui.InputText(config.get('site').get('site'), key='site',
                       size=(32, 1), disabled=True), ],
        [gui.Text('Additional Email Tags:',
                  size=(None, 1), justification='left'), ],
        [gui.Multiline(config.get(
            'exchange_client_config').get('tags'), key='tags', size=(32, 3),
            auto_size_text=True, do_not_clear=True,
            enable_events=True), ], ]

    conf_emails_col = [
        [gui.Text('Exchange Accounts:',  justification='left'), ],
        [gui.Table(
            [[None, None, None, None, None, None]],
            headings=['domain', 'username', 'password', 'smtp',
                      'autodiscover', 'autodiscover server'], key='exc_accs',
            auto_size_columns=True, display_row_numbers=True), ],
        [gui.Text('Witness Addresses:', justification='left'), ],
        [gui.Multiline(
            ', '.join(
                config.get('exchange_client_config').get('witness_addresses')),
            size=(96, 1), key='witness_addresses', disabled=True), ], ]

    config_frame = [
        [gui.Checkbox('Load Config from Server',
                      default=base_config.get('use_cfg_srv'),
                      key='use_cfg_srv', enable_events=True),
         gui.Text('Config Server Address', justification='left'),
         gui.InputText(base_config.get('cfg_srv_ip'), key='cfg_srv_ip',
                       size=(12, 1), do_not_clear=True, enable_events=True),
         gui.Text('Config Server Port', justification='left'),
         gui.InputText(base_config.get('cfg_srv_port'), key='cfg_srv_port',
                       size=(5, 1), do_not_clear=True, enable_events=True),
         gui.Text('Connection timeout'),
         gui.InputText(base_config.get('cfg_srv_conn_timeout'),
                       key='cfg_srv_conn_timeout', size=(3, 1),
                       do_not_clear=True, enable_events=True),
         gui.Text('Read timeout'),
         gui.InputText(base_config.get('cfg_srv_read_timeout'),
                       key='cfg_srv_read_timeout', size=(3, 1),
                       do_not_clear=True, enable_events=True),
         gui.Text('', size=(39, 1)),
         gui.Button('Save local config', key='save_config',
                    disabled=True),
         gui.Button('Reset local config', key='reset_config',
                    disabled=False), ],
        [gui.Text(config.get('load_status'))],
    ]

    mail_check_frame = [
        [
            gui.Text(
                ('Configuration changes are not preserved across startups.'
                 ' To persist changes, edit the configuration on the server at')),
            gui.InputText(
                '{}://{}:{}/admin/mail_collector/exchangeconfiguration/?q={}'.
                format(
                    HTTP_PROTO, base_config.get('cfg_srv_ip'),
                    base_config.get('cfg_srv_port'),
                    config.get('exchange_client_config').get('config_name')),
                disabled=True, size=(80, 1), key='bot_cfg_url'),
            gui.Button('Refresh config from server', key='reload_config',
                       disabled=False),
        ],
        [
            gui.Column(conf_labels_col),
            gui.Column(conf_values_col),
            gui.Column(conf_emails_col),
        ],
    ]

    layout = [
        [gui.Frame('Control',
                   control_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Local configuration',
                   config_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Exchange verification configuration',
                   mail_check_frame, title_color='darkblue', font='Any 12'), ],
        [gui.Frame('Output',
                   output_frame, title_color='darkblue', font='Any 12'), ]]

    window.Layout(layout).Finalize()

    return base_config, config, window

# pylint: enable=unnecessary-comprehension


def _accounts_to_table(accounts, window):
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
    listed_accounts = []

    for account in accounts:

        _account = []
        _account.append(account.get('domain_account').get('domain'))
        _account.append(account.get('domain_account').get('username'))
        _account.append(account.get('domain_account').get('password'))
        _account.append(account.get('smtp_address'))
        _account.append(account.get('exchange_autodiscover'))
        _account.append(account.get('autodiscover_server'))

        listed_accounts.append(_account)

    window.FindElement('exc_accs').Update(listed_accounts)


def next_run_in(next_run_at):
    """
    update the time counter for the next :func:`mail_check` call

    :arg `datetime.datetime` next_run_at: the moment for the next
        :func:`mail_check` call

        This moment is re-evaluated every time the :func:`mail_check` is called
        and it is stored in a state variable in the :func:`main` function.

    :returns: a :class:`tuple` in minutes, seconds format that represents the
        time left until the next call of the :func:`mail_check`
    """
    mins, secs = divmod((next_run_at - datetime.now()).total_seconds(), 60)
    return '{} minutes, {} seconds'.format(int(mins), int(secs))


def mail_check(config, window, update_window_queue):
    """
    start the `threading.Thread` where the Exchange verification op is
    executed

    This function is called from the OnClickUp event of the
    ``RUn Mail Check Now`` `PySimpleGUI.Button`.

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
    window.FindElement('mailcheck').Update(disabled=True)
    if not window.FindElement('run').Disabled:
        window.FindElement('run').Update(disabled=True)
    if not window.FindElement('pause').Disabled:
        window.FindElement('pause').Update(disabled=True)
    window.FindElement('status').Update('running mail check')
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update(
        '{:%c}: running mail check\n'.format(datetime.now()), append=True)
    window.FindElement('output').Update(disabled=True)

    thr = threading.Thread(target=_mail_check, args=(
        update_window_queue, dict(config)))
    thr.start()


def _mail_check(update_window_queue, config):
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
    witness_messages = WitnessMessages(
        console_logger=update_window_queue, **config)
    witness_messages.verify_receive()


def do_save_config(window):
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
    items = [
        ('use_cfg_srv', bool(window.FindElement('use_cfg_srv').Get())),
        ('cfg_srv_ip', window.FindElement('cfg_srv_ip').Get()),
        ('cfg_srv_port', int(window.FindElement('cfg_srv_port').Get())),
        ('cfg_srv_conn_timeout',
         int(window.FindElement('cfg_srv_conn_timeout').Get())),
        ('cfg_srv_read_timeout',
         int(window.FindElement('cfg_srv_read_timeout').Get())),
    ]

    save_base_configuration(dict_config=collections.OrderedDict(items))


def _witness_emails_from_list(witness_emails, window):
    """
    populate the ``GUI`` element used for showing
    :class:`mail_collector.models.WitnessEmail` instances used in the
    main configuration

    This ``GUI`` element is accepting only :class:`str` data while the
    :class:`mail_collector.models.WitnessEmail` data is provided as a
    :class:`list`.

    """
    window.FindElement('witness_addresses').Update(', '.join(witness_emails))


def do_reload_config(window):
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
    items = [
        ('use_cfg_srv', bool(window.FindElement('use_cfg_srv').Get())),
        ('cfg_srv_ip', window.FindElement('cfg_srv_ip').Get()),
        ('cfg_srv_port', int(window.FindElement('cfg_srv_port').Get())),
        ('cfg_srv_conn_timeout',
         int(window.FindElement('cfg_srv_conn_timeout').Get())),
        ('cfg_srv_read_timeout',
         int(window.FindElement('cfg_srv_read_timeout').Get())),
    ]

    current_base_config = collections.OrderedDict(items)
    config = load_config(current_base_config=current_base_config)

    window.FindElement('bot_cfg_url').Update(
        '{}://{}:{}/admin/mail_collector/mailhost/?q={}'.format(
            HTTP_PROTO, current_base_config.get('cfg_srv_ip'),
            current_base_config.get('cfg_srv_port'),
            config.get('host_name'))
    )
    window.FindElement('autorun').Update(
        config.get('exchange_client_config').get('autorun')
    )
    window.FindElement('debug').Update(
        config.get('exchange_client_config').get('debug')
    )
    window.FindElement('check_mx').Update(
        config.get('exchange_client_config').get('check_mx')
    )
    window.FindElement('email_subject').Update(
        config.get('exchange_client_config').get('email_subject')
    )
    window.FindElement('mail_check_period').Update(
        config.get('exchange_client_config').get('mail_check_period')
    )
    window.FindElement('ascii_address').Update(
        config.get('exchange_client_config').get('ascii_address')
    )
    window.FindElement('utf8_email').Update(
        config.get('exchange_client_config').get('utf8_email')
    )
    window.FindElement('check_mx_timeout').Update(
        config.get('exchange_client_config').get('check_mx_timeout')
    )
    window.FindElement('min_wait_receive').Update(
        config.get('exchange_client_config').get('min_wait_receive')
    )
    window.FindElement('backoff_factor').Update(
        config.get('exchange_client_config').get('backoff_factor')
    )
    window.FindElement('max_wait_receive').Update(
        config.get('exchange_client_config').get('max_wait_receive')
    )
    window.FindElement('site').Update(config.get('site').get('site'))
    window.FindElement('tags').Update(
        config.get('exchange_client_config').get('tags')
    )
    _accounts_to_table(config.get(
        'exchange_client_config').get('exchange_accounts'), window)
    _witness_emails_from_list(
        config.get('exchange_client_config').get('witness_addresses'), window)

    return config


def do_reset_config(window):
    """
    reload the basic configuration active in the ``GUI`` with the
    values defined in the :attr:`mail_borg.config.INI_DEFAULTS`

    Note that these defaults, particularly the value of the ``cfg_srv_ip``
    (the address of the ``SOC Automation server``) may be out of date.

    This function is invoked by the OnCLickUp event of the ``Reset local
    config`` `PySimpleGUI.Button` element.

    :arg `PySimpleGUI.window` window: the window objects associated with
        the ``GUI`` interface

    """
    reset_base_configuration()
    base_config = load_base_configuration()
    for key, value in base_config.items():
        window.FindElement(key).Update(value)

    return base_config


def _set_autorun(window):
    """
    calculate the value of the :attr:`main.autorun` state variable

    :returns: ``True`` or ``False``

    """
    autorun = window.FindElement('autorun').Get()
    if autorun:
        window.FindElement('pause').Update(disabled=False)
        window.FindElement('run').Update(disabled=True)
    else:
        window.FindElement('pause').Update(disabled=True)
        window.FindElement('run').Update(disabled=False)
        window.FindElement('status').Update(
            'automated mail check execution is paused')
    return autorun


def _do_pause(window):
    """
    update various ``GUI`` elements to reflect the :attr:`main.autorun` state
    variable
    """
    window.FindElement('status').Update(
        'automated mail check execution is paused')
    window.FindElement('pause').Update(disabled=True)
    window.FindElement('run').Update(disabled=False)


def _dirty_window(window):
    """
    update various ``GUI`` elements to reflect the
    :attr:`main.config_is_dirty` state variable
    """
    window.FindElement('save_config').Update(disabled=False)
    window.FindElement('reset_config').Update(disabled=False)


def _do_clear(window):
    """
    clear the data from ``output`` `PySimpleGUI.Multiline` element

    This function is invoked in the OnClickUp event of the ``Clear execution
    data`` `PySimpleGUI.Button` element
    """
    window.FindElement('output').Update(disabled=False)
    window.FindElement('output').Update('')
    window.FindElement('output').Update(disabled=True)


def main():  # pylint: disable=too-many-branches,too-many-statements
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
    editable = ['use_cfg_srv', 'cfg_srv_ip', 'cfg_srv_port',
                'cfg_srv_conn_timeout', 'cfg_srv_conn_timeout']

    update_window_queue = Queue(maxsize=500)
    base_config, config, window = get_window()
    _accounts_to_table(
        config.get('exchange_client_config').get('exchange_accounts'), window)

    config_is_dirty = False
    next_run_at = datetime.now() + \
        timedelta(minutes=int(window.FindElement('mail_check_period').Get()))
    autorun = _set_autorun(window)

    while True:
        event, values = window.Read(timeout=0)

        if values is None or event == 'Exit':
            if config_is_dirty:
                save = gui.PopupYesNo(
                    'Save configuration?',
                    'There are unsaved changes'
                    ' in the application configuration.'
                    ' Do you wish to save them?')

                if save == 'Yes':
                    do_save_config(config)

            break

        while not update_window_queue.empty():
            msg = update_window_queue.get_nowait()
            if msg[0] in ['output']:
                window.FindElement('output').Update(disabled=False)
                window.FindElement('output').Update(msg[1], append=True)
                window.FindElement('output').Update(disabled=True)
                window.FindElement('status').Update('mail check in progress')

            if msg[0] in ['abort']:
                window.FindElement('output').Update(disabled=False)
                window.FindElement('output').Update(
                    '\nmail check aborted\n', append=True)
                window.FindElement('output').Update(disabled=True)
                window.FindElement('status').Update(
                    'mail check aborted. please verify the configuration')
                window.FindElement('autorun').Update(value=False)

            if msg[0] in ['control']:
                window.FindElement('output').Update(disabled=False)
                window.FindElement('output').Update('\nmail check complete\n',
                                                    append=True)
                window.FindElement('output').Update(disabled=True)
                window.FindElement('mail_check_period').Update(disabled=False)
                window.FindElement('mailcheck').Update(disabled=False)
                if autorun:
                    window.FindElement('pause').Update(disabled=False)
                    next_run_at = datetime.now() + \
                        timedelta(minutes=int(window.FindElement(
                            'mail_check_period').Get()))
                    window.FindElement('status').Update(
                        'next mail check run in {}'.format(
                            next_run_in(next_run_at))
                    )
                else:
                    window.FindElement('run').Update(disabled=False)
                    window.FindElement('status').Update(
                        'automated mail check execution is paused')

        if event in editable:
            config_is_dirty = True
            if not isinstance(base_config[event], (bool, int)):
                base_config[event] = window.FindElement(event).Get().\
                    replace('\n', '')
            else:
                base_config[event] = window.FindElement(event).Get()

            _dirty_window(window)

            if event == 'autorun':
                autorun = _set_autorun(window)

            if event == 'mail_check_period':
                next_run_at = datetime.now() + \
                    timedelta(
                        minutes=int(
                            window.FindElement('mail_check_period').Get()))

        if event == 'save_config':
            do_save_config(window)
            window.FindElement('save_config').Update(disabled=True)
            config_is_dirty = False

        if event == 'reset_config':
            base_config = do_reset_config(window)

        if event == 'reload_config':
            config = do_reload_config(window)

        if event == 'clear':
            _do_clear(window)

        if autorun:
            window.FindElement('pause').Update(disabled=False)
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

            if next_run_at <= datetime.now():
                mail_check(config=config, window=window,
                           update_window_queue=update_window_queue)
                next_run_at = datetime.now() + \
                    timedelta(minutes=int(window.FindElement(
                        'mail_check_period').Get()))

        if event == 'mailcheck':
            mail_check(config=config, window=window,
                       update_window_queue=update_window_queue)
            next_run_at = datetime.now() + \
                timedelta(minutes=int(window.FindElement(
                    'mail_check_period').Get()))

            if autorun:
                window.FindElement('run').Update(disabled=True)
                window.FindElement('pause').Update(disabled=False)
                window.FindElement('status').Update(
                    'next mail check run in {}'.format(
                        next_run_in(next_run_at)))
            else:
                window.FindElement('run').Update(disabled=False)
                window.FindElement('pause').Update(disabled=True)
                window.FindElement('status').Update(
                    'automated mail check execution is paused')

        if event == 'pause':
            autorun = False
            _do_pause(window)

        if event == 'run':
            autorun = True
            window.FindElement('run').Update(disabled=True)
            window.FindElement('pause').Update(disabled=False)
            window.FindElement('status').Update(
                'next mail check run in {}'.format(next_run_in(next_run_at)))

        time.sleep(1)

    # Broke out of main loop. Close the window.

    window.Close()


if __name__ == '__main__':

    if sys.platform != 'win32':
        # me only like windows, booooo
        raise OSError('%s will not work on %s' % (__name__, sys.platform))

    main()
