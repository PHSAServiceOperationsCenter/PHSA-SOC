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

The development branch has been named `development`. All feature branches
must originate from this branch. It is recommended that all feature branches be
named using the **feature-$FeatureName** convention. It is also recommended that
the first commit on a feature branch include the link to the `Trello board
<https://trello.com/phsasoc>`__ describing the functionality that is implemented
by the feature branch.

All `Hotfix branches
<https://nvie.com/posts/a-successful-git-branching-model/#hotfix-branches>`__
must originate off `master` or off a `Release branch
<https://nvie.com/posts/a-successful-git-branching-model/#release-branches>`__.
A `hotfix` branch must be named using the **hotfix-$HotfixName** convention.
It is recommended that the first commit on a `hotfix` branch include the link
to the `Trello board <https://trello.com/phsasoc>`__ describing the bug that the
branch is addressing.

Commit Process
--------------

1. Sanity test code locally.
2. Deploy code on test server and sure it runs correctly. It may be necessary to wait overnight to allow scheduled processes to run.
3. Run Pylint and Bandit on modified files, and make changes as appropriate (create comments for suggested changes that are being ignored, either explaining why they are inappropriate [eg modifying functions inherited from Django whose arguments are not used in our code] or a TODO explaining the problem and [if possible] potential solutions)
4. Open a pull request via GitHub and assign reviewers (or get code re-reviewed if modifying code in response to feedback).
5. Respond to reviewer comments, modifying code and returning to step one as necessary.
6. Code will be merged as per above.

.. todo ::

    Set up automated tests. Would be a step between 1 and 2.