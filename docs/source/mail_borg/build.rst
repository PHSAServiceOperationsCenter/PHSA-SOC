Building the Mail Borg Application
==================================

The :ref:`Mail Borg Client Application` is written in `Python
<https://www.python.org/about/>`_ and under most circumstances `Python
<https://www.python.org/about/>`_ applications have a lot of depedencies and
are relatively hard to deploy.

Compiling
---------

It is possible to package a complete `Python
<https://www.python.org/about/>`_ application into a single executable file.
The executabel will contain all the dependencies required by the application,
including the `Python <https://www.python.org/about/>`_ interpreter.

We are using the `PyInstaller
<https://pyinstaller.readthedocs.io/en/stable/index.html>`__ package.

The `PyInstaller <https://pyinstaller.readthedocs.io/en/stable/index.html>`__
package must be installed in the `virtual environment
<https://docs.python.org/3.6/tutorial/venv.html?highlight=virtual%20environments>`__
used for developing the :ref:`Mail Borg Client Application`. Currently, there
is a `pip requirements file
<https://pip.pypa.io/en/stable/user_guide/?highlight=requirements#requirements-files>`__
under source control that is used for Windows specific requirements named
requirements_win.txt and the `PyInstaller
<https://pyinstaller.readthedocs.io/en/stable/index.html>`__ package is
referenced within said requirements file. To update the ``Python`` packages in
the environment, execute:

.. code-block:: ps1con

    Windows PowerShell
    Copyright (C) Microsoft Corporation. All rights reserved.
    
    Try the new cross-platform PowerShell https://aka.ms/pscore6
    
    PS C:\Users\serban> .\Envs\carmina\Scripts\activate.ps1
    (carmina) PS C:\Users\serban> cd .\phsa-work\sbin\p_soc_auto\
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto> cd .\mail_borg\
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg> cd ..
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto> pip install -r .\requirements_win.txt
    Requirement already satisfied: alabaster==0.7.12 in c:\users\serban\envs\carmina\lib\site-packages (from -r .\requirements_win.txt (line 1)) (0.7.12)
    Requirement already satisfied: altgraph==0.16.1 in c:\users\serban\envs\carmina\lib\site-packages (from -r .\requirements_win.txt (line 2)) (0.16.1)
    ...
    Requirement already satisfied: PyInstaller==3.5 in c:\users\serban\envs\carmina\lib\site-packages (from -r .\requirements_win.txt (line 104)) (3.5)
    ...
    WARNING: You are using pip version 19.2.1, however version 19.2.3 is available.
    You should consider upgrading via the 'python -m pip install --upgrade pip' command.
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto> 


Here is a sequence of commands that will result in compiling the
:ref:`Mail Borg Client Application`.

.. code-block:: ps1con

    Windows PowerShell
    Copyright (C) Microsoft Corporation. All rights reserved.
    
    Try the new cross-platform PowerShell https://aka.ms/pscore6
    
    PS C:\Users\serban> .\Envs\carmina\Scripts\activate.ps1
    (carmina) PS C:\Users\serban> cd .\phsa-work\sbin\p_soc_auto\mail_borg\
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg> python -m PyInstaller --onefile --console --uac-admin --uac-uiaccess .\mail_borg_gui.py --clean
    78 INFO: PyInstaller: 3.5
    78 INFO: Python: 3.6.5
    93 INFO: Platform: Windows-10-10.0.18362-SP0
    93 INFO: wrote C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\mail_borg_gui.spec
    93 INFO: UPX is not available.
    109 INFO: Removing temporary files and cleaning cache in C:\Users\serban\AppData\Roaming\pyinstaller
    109 INFO: Extending PYTHONPATH with paths
    ['C:\\Users\\serban\\phsa-work\\sbin\\p_soc_auto',
     'C:\\Users\\serban\\phsa-work\\sbin\\p_soc_auto\\mail_borg']
    109 INFO: checking Analysis
    109 INFO: Building Analysis because Analysis-00.toc is non existent
    109 INFO: Initializing module dependency graph...
    124 INFO: Initializing module graph hooks...
    124 INFO: Analyzing base_library.zip ...
    4515 INFO: running Analysis Analysis-00.toc
    4531 INFO: Adding Microsoft.Windows.Common-Controls to dependent assemblies of final executable
      required by C:\Users\serban\Envs\carmina\Scripts\python.exe
    4843 INFO: Caching module hooks...
    4859 INFO: Analyzing C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\mail_borg_gui.py
    5859 INFO: Processing pre-safe import module hook   urllib3.packages.six.moves
    7906 INFO: Processing pre-safe import module hook   six.moves
    10046 INFO: Processing pre-find module path hook   distutils
    10046 INFO: distutils: retargeting to non-venv dir 'c:\\program files\\python36\\Lib\\distutils'
    16358 INFO: Loading module hooks...
    16358 INFO: Loading module hook "hook-certifi.py"...
    16358 INFO: Loading module hook "hook-cryptography.py"...
    16717 INFO: Loading module hook "hook-distutils.py"...
    16717 INFO: Loading module hook "hook-dns.rdata.py"...
    17375 INFO: Loading module hook "hook-encodings.py"...
    17468 INFO: Loading module hook "hook-lib2to3.py"...
    17500 INFO: Loading module hook "hook-lxml.etree.py"...
    17500 INFO: Loading module hook "hook-pkg_resources.py"...
    17967 INFO: Processing pre-safe import module hook   win32com
    18218 INFO: Loading module hook "hook-pydoc.py"...
    18218 INFO: Loading module hook "hook-pygments.py"...
    20532 INFO: Loading module hook "hook-pythoncom.py"...
    20905 INFO: Loading module hook "hook-pytz.py"...
    20967 INFO: Loading module hook "hook-pywintypes.py"...
    21359 INFO: Loading module hook "hook-shelve.py"...
    21359 INFO: Loading module hook "hook-sysconfig.py"...
    21359 INFO: Loading module hook "hook-win32com.py"...
    21843 INFO: Loading module hook "hook-xml.dom.domreg.py"...
    21843 INFO: Loading module hook "hook-xml.etree.cElementTree.py"...
    21843 INFO: Loading module hook "hook-xml.py"...
    21859 INFO: Loading module hook "hook-_tkinter.py"...
    22046 INFO: checking Tree
    22046 INFO: Building Tree because Tree-00.toc is non existent
    22046 INFO: Building Tree Tree-00.toc
    22249 INFO: checking Tree
    22249 INFO: Building Tree because Tree-01.toc is non existent
    22249 INFO: Building Tree Tree-01.toc
    22311 INFO: Looking for ctypes DLLs
    22358 INFO: Analyzing run-time hooks ...
    22374 INFO: Including run-time hook 'pyi_rth_multiprocessing.py'
    22389 INFO: Including run-time hook 'pyi_rth__tkinter.py'
    22389 INFO: Including run-time hook 'pyi_rth_certifi.py'
    22389 INFO: Including run-time hook 'pyi_rth_pkgres.py'
    22405 INFO: Including run-time hook 'pyi_rth_win32comgenpy.py'
    22420 INFO: Looking for dynamic libraries
    23017 INFO: Looking for eggs
    23017 INFO: Using Python library C:\Users\serban\Envs\carmina\Scripts\python36.dll
    23017 INFO: Found binding redirects:
    []
    23033 INFO: Warnings written to C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\build\mail_borg_gui\warn-mail_borg_gui.txt
    23158 INFO: Graph cross-reference written to C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\build\mail_borg_gui\xref-mail_borg_gui.html
    23280 INFO: checking PYZ
    23280 INFO: Building PYZ because PYZ-00.toc is non existent
    23280 INFO: Building PYZ (ZlibArchive) C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\build\mail_borg_gui\PYZ-00.pyz
    24874 INFO: Building PYZ (ZlibArchive) C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\build\mail_borg_gui\PYZ-00.pyz completed successfully.
    24921 INFO: checking PKG
    24921 INFO: Building PKG because PKG-00.toc is non existent
    24921 INFO: Building PKG (CArchive) PKG-00.pkg
    35468 INFO: Building PKG (CArchive) PKG-00.pkg completed successfully.
    35499 INFO: Bootloader C:\Users\serban\Envs\carmina\lib\site-packages\PyInstaller\bootloader\Windows-64bit\run.exe
    35499 INFO: checking EXE
    35499 INFO: Building EXE because EXE-00.toc is non existent
    35499 INFO: Building EXE from EXE-00.toc
    35515 INFO: Appending archive to EXE C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist\mail_borg_gui.exe
    35748 INFO: Building EXE from EXE-00.toc completed successfully.
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg> cd dist
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist> dir
    
    
        Directory: C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist
    
    
    Mode                LastWriteTime         Length Name
    ----                -------------         ------ ----
    d-----       2019-09-16     11:56                mail_borg_gui
    -a----       2019-08-20     10:53            123 mail_borg.ini
    -a----       2019-09-23     12:13       21124100 mail_borg_gui.exe
    -a----       2019-09-16     11:57       20650575 mail_borg_gui.zip
    
    
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist> 

As show in the ``dir`` listing, there is now a file named
``mail_borg_gui.exe`` under the ``dist`` directory.    
:note:

    We assume that the virtual environment is named ``carmina`` and that it
    is installed under ``%HOMEPATH%\Envs\``.

Signing
-------

It is good practice to sign Windows executables. Continuing from the section
above:

.. code-block:: ps1con

    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist> Set-AuthenticodeSignature .\mail_borg_gui.exe -Certificate (Get-ChildItem Cert:\CurrentUser\my -CodeSigningCert)
    
    
        Directory: C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist
    
    
    SignerCertificate                         Status                                 Path
    -----------------                         ------                                 ----
    16B7581F406E8614EFDA8FDA3F68A5E4ABBD7261  Valid                                  mail_borg_gui.exe
    
    
    (carmina) PS C:\Users\serban\phsa-work\sbin\p_soc_auto\mail_borg\dist>    
    
The ``mail_borg_gui.exe`` is now signed.

Self-signed certificate
^^^^^^^^^^^^^^^^^^^^^^^

In an ideal world, one is supposed to sign an executable with a trusted
certificate but life is cruel.

Therefore, one will generate one's own self-signed certificate as shown
below. Note that this is a PowerShell session with Administrator privileges.

Create the certificate:

.. code-block::

    PS C:\Users\serban> New-SelfSignedCertificate -DnsName serban.teodorescu@phsa.ca -Type CodeSigning -CertStoreLocation cert:\CurrentUser\My
    
Export the certificate:

.. code-block::

    PS C:\Users\serban> Export-Certificate -Cert (Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert)[0] -FilePath mail_borg_gui_sig.crt
    
Import the certificate to the TrustedPublisher cert store:

.. code-block::

    PS C:\Users\serban> Import-Certificate -FilePath .\mail_borg_gui_sig.crt -Cert Cert:\CurrentUser\TrustedPublisher
    
Import the certificate to the Root cert store:

.. code-block::

    PS C:\Users\serban> Import-Certificate -FilePath .\mail_borg_gui_sig.crt -Cert Cert:\CurrentUser\Root

The file with the signing certificate is now present under
``C:\users\serban\mail_borg_gui_sig.crt``.

The detailed documentation for handling self-signed certificates in Windows is
available from `Microsoft <https://www.microsoft.com/en-ca/>`_ at 
`New-SelfSignedCertificate
<https://docs.microsoft.com/en-us/powershell/module/pkiclient/new-selfsignedcertificate?view=win10-ps>`_.

Deploying
---------

The following files are needed in order to deploy the :ref:`Mail Borg Client
Application` to a remote bot:

* ``mail_borg_gui.exe``

* ``mail_borg.ini``

* ``mail_borg_gui_sig.crt``

The easiest way to deploy is to create an archive with the ``exe`` and the
``ini`` file and download it on the remote bot. Extract the archive and copy
the resulting folder to a suitable location.

Before running the executable, one must tell the bot that the signing
certificate is to be trusted. Download the ``crt`` file that was used to sign
the :ref:`Mail Borg Client Application` executable on the remote bot and
install it.
To install the certificate, one can use the last two PowerShell commands from
the previous section, or one can right-click the ``crt`` file in a ``File
Manager`` window and choose the ``Install`` menu item.

A detailed deployment procedure is documented under `SOC - Procedural Guide -
Exchange Monitoring Client Version 2
<http://our.healthbc.org/sites/gateway/team/TSCSTHub/_layouts/15/WopiFrame2.aspx?sourcedoc=/sites/gateway/team/TSCSTHub/Shared Documents/Drafts/SOC - Procedural Guide - Exchange Monitoring Client Version 2.doc&action=default>`_.

The latest version of the :ref:`Mail Borg Client Application` installation
archive is available under `Exchange Monitoring Client Version 2
<http://our.healthbc.org/sites/gateway/team/TSCSTHub/Shared%20Documents/Forms/AllItems.aspx?RootFolder=%2Fsites%2Fgateway%2Fteam%2FTSCSTHub%2FShared%20Documents%2FTools%2FExchangeMonitoring%2Fversion%5F2&FolderCTID=0x01200049BD2FC3E2032F40A74A4A7D97D53F7A&View=%7BC5878F2F%2DACBC%2D450F%2DAF48%2D52726B6E8F63%7D>`_.
We are not allowed to save certificate files on the Sharepoint server.

Contact `Serban Teodorescu <mailto:serban.teodorescu@phsa.ca>`_ for access to
the ``crt`` file.

Running
-------

The :ref:`Mail Borg Client Application` must run with ``Adminstrator``
privileges. Navigate to the folder where one has installed the application.

Open the mail_borg.ini file and verify that the ``cfg_srv_ip`` property is
pointing to the correct ``Soc Automation server`` and that the ``use_cfg_srv``
is set to ``True``. Edit and save the file if necessary, then close it.

Right-click the ``exe`` file and choose to run it as admin. Tell ``Norton`` to
sit down and shut up. Click the ``Run mail check`` button or wait for the
program to execute the mail check automatically as configured.

It is highly recommended to create a start-up task for this application.

The `SOC - Procedural Guide -
Exchange Monitoring Client Version 2
<http://our.healthbc.org/sites/gateway/team/TSCSTHub/_layouts/15/WopiFrame2.aspx?sourcedoc=/sites/gateway/team/TSCSTHub/Shared Documents/Drafts/SOC - Procedural Guide - Exchange Monitoring Client Version 2.doc&action=default>`_.
is providing details about running and configuring the :ref:`Mail Borg Client
Application`.