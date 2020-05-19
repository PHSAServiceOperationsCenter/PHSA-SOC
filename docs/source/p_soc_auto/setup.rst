Set-Up
======

This page provides an overview of how to set-up the different systems
that are required in developing, and running, the SOC Automation Framework.

Development System (Server)
---------------------------

1. Install Python.
2. Checkout the codebase from `GitHub <https://github.com/PHSAServiceOperationsCenter/PHSA-SOC>`__.
3. RabbitMQ
4. LogStash
5. MemCached
6. Set-up Celery Tasks
7. Set-up necessary log folders (so that the application has the right permissions to access them)


Development System (Laptop)
---------------------------

Any editor may be used to work on the code base, however it is recommended to use one that can
be integrated with the various tools we use to maintain our development. These include: Git, pylint,
and bandit.

1. Install `Python <https://www.python.org/downloads/>`__. See requirements for current version (3.7 for PyInstaller).
Note that the majority of software is being run from the Linux server, so this is used for building
the windows application(s), and providing your editor with the appropriate libraries (to do code lookups).
2. Install your editor of choice.
3. Install wheels for sql libraries manually from some university site (did i write this down somewhere?)
3. (should be part of reqs) Install other necessary 3rd-party tools. See `Git <https://git-scm.com/download/win>`__. pylint and bandit
can be install using `pip <https://packaging.python.org/tutorials/installing-packages/>`__.
4. ``pip install -r requirements-win.txt`` (install cryptography separately with admin(?) and manually download and install mysql thing to avoid needed windows binaries)
