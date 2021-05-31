Source Control
==============

The :ref:`SOC Automation Project` code is under source control on `GitHub
<https://github.com/PHSAServiceOperationsCenter/PHSA-SOC>`__. If one needs write
access to this repository, one must contact `James Reilly
<mailto:james.reilly@phsa.ca>`__.

Starting with `PHSA-SOC release 1.0.0
<https://github.com/PHSAServiceOperationsCenter/PHSA-SOC/releases/tag/1.0.0>`__,
the SOC development team has decided to use the `Gitflow
<https://nvie.com/posts/a-successful-git-branching-model/>`__ model for
managing the development process.

The development branch has been named "development". All feature branches
must originate from this branch. It is recommended that
the first commit on a feature branch include the link to the `Jira
<https://phsasocapp.atlassian.net/secure/BrowseProjects.jspa>`__  issue describing
the functionality that is being implemented.

All `Hotfix branches
<https://nvie.com/posts/a-successful-git-branching-model/#hotfix-branches>`__
must originate off "master" or off a `Release branch
<https://nvie.com/posts/a-successful-git-branching-model/#release-branches>`__.
A "hotfix" branch must be named using the **hotfix-$HotfixName** convention.
It is recommended that the first commit on a "hotfix" branch include the link
to the issue describing the bug that the branch is addressing.

Commit Process
--------------

1. Sanity test code locally.
2. Run Pylint and Bandit on modified files, and make changes as appropriate (create comments for ignored suggestions, either explaining why they are inappropriate or a TODO explaining the problem and potential solutions)
3. Take a snapshot of database on the production server. `mysqldump phsa_database -u phsa_db_user -p > snapshot[date].sql`
4. Copy database snapshot onto the test server and copy into database, by dropping all the database rows and then running `mysql phsa_database -u phsa_db_user -p < snapshot[date].sql`
5. Deploy code to test server, by pulling the development branch.
6. Run the Django migrations to update database: `python manage.py migrate` (from the base project directory)
7. Restart the necessary services, at minumum run `restart_celery_services`. It may be necessary to wait overnight to allow scheduled processes to run and verify results.
8. Open a pull request to the next version branch via GitHub and assign reviewers (or get code re-reviewed if modifying code in response to feedback).
9. Respond to reviewer comments, modifying code and returning to step one as necessary.
10. Code will be merged as per above.

.. todo ::

    Set up automated tests to be run on development machine. Would be a step between 1 and 2.