Source Control
==============

The :ref:`SOC Automation Project` code is under source control on `GitHub
<https://github.com/PHSAServiceOperationsCenter/PHSA-SOC>`__. If one needs write
access to this repository, one must contact `James Reilly
<mailto:james.reilly@phsa.ca>`__.

Starting with `PHSA-SOC release 1.0.0
<https://github.com/PHSAServiceOperationsCenter/PHSA-SOC/releases/tag/1.0.0>`__,
the SOC development team (yours, humbly) has decided to use the `Gitflow
<https://nvie.com/posts/a-successful-git-branching-model/>`__ model for
managing the development process.

The development branch has been named `development` (duh). All feature branches
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