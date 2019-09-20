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
<https://pyinstaller.readthedocs.io/en/stable/index.html>`_ package.

The `PyInstaller <https://pyinstaller.readthedocs.io/en/stable/index.html>`_
package must be installed in the `virtual environment
<https://docs.python.org/3.6/tutorial/venv.html?highlight=virtual%20environments>`_
used for developing the :ref:`Mail Borg Client Application`.
For example:

.. code-block:: ps1

    

Signing
-------

Self-signed certificate
^^^^^^^^^^^^^^^^^^^^^^^

Deploying
---------