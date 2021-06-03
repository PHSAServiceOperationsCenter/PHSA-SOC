Set-Up
======

This page provides an overview of how to set-up the different systems
that are required in developing, and running, the SOC Automation Framework.

Development System (Server)
---------------------------

#. Install Python.
#. Checkout the codebase from `GitHub <https://github.com/PHSAServiceOperationsCenter/PHSA-SOC>`__.
#. RabbitMQ
#. LogStash
#. MemCached
#. Set-up Celery Tasks
#. Set-up necessary log folders (so that the application has the right permissions to access them)


Development System (Laptop)
---------------------------

Any editor may be used to work on the code base, however it is recommended to use one that can
be integrated with the various tools we use to maintain our development. These include: Git, pylint,
and bandit.

.. note:: The majority of software is being run from the Linux server, so this setup is only needed if you
          are working on the windows application(s), (though it is also useful for being able to look at the code for imported libraries).

#. Install `Python <https://www.python.org/downloads/>`__. See requirements for current version (3.7 for PyInstaller).
#. Install your editor of choice.
#. Install wheels for sql libraries manually. These are hosted at a couple places online.
#. Install other necessary 3rd-party tools. See `Git <https://git-scm.com/download/win>`__. pylint and bandit
   can be install using `pip <https://packaging.python.org/tutorials/installing-packages/>`__.
#. ``pip install -r <requirements file>`` (install cryptography separately with admin rights and manually download and install mysql library to get windows libraries)

.. todo:: Add 3rd-party tools to the requirements file