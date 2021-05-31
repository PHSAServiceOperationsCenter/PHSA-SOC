SFTP monitoring application
===========================

This application monitors the `SFTP servers <https://en.wikipedia.org/wiki/SSH_File_Transfer_Protocol>`_ managed by
PHSA.

The application uploads an empty text file to the SFTP server and verifies that the operation completes successfully.

There are seperate servers for accessing SFTP on PHSA's internal network, and externally.
Currently only the internal network is being tested.

.. toctree::
   :maxdepth: 2

   modules.rst
