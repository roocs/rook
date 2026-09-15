.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

Please read the Birdhouse [Developer Guide](https://birdhouse.readthedocs.io/en/latest/guide_dev.html) and this document to get started.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/roocs/rook/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

rook could always use more documentation, whether as part of the official rook docs, in docstrings, or even on the web in blog posts, articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/roocs/rook/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `rook` for local development.

1. Fork the `rook` repo on GitHub.
2. Clone your fork locally:

.. code-block:: console

    $ git clone git@github.com:your_name_here/rook.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development:

.. code-block:: console

    $ mkvirtualenv rook
    $ cd rook/
    $ python setup.py develop

4. Create a branch for local development:

.. code-block:: console

    $ git checkout -b name-of-your-bugfix-or-feature

Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox:

.. code-block:: console

    $ make lint
    $ make test
    # or
    $ make test-all

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub:

.. code-block:: console

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring, and add the feature to the list in README.rst.
3. The pull request should work for all supported Python versions. Check https://github.com/roocs/rook/actions and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests:

.. code-block:: console

    $ pytest tests.test_rook



Deploying
---------

A reminder for the maintainers on how to deploy a new version.
Make sure the release branch includes the changelog, refreshed Conda artifacts, and version metadata.
Push and merge that release commit, then tag the merged commit on ``main``:

  * Make sure all code changes have been committed and pushed to `main` (including an entry in CHANGELOG.rst).
  * Create a new branch and Pull Request (`prepare-release-vX.Y.Z`).
  * Update ``CHANGELOG.rst`` history under `unreleased`.
  * Dry run: ``bump-my-version bump major|minor|patch|build --dry-run --verbose``
  * Do it for real: ``bump-my-version bump major|minor|patch``
  * Prepare release version: ``bump-my-version bump release``
  * Push it: ``git push``
  * Merge your Pull Request to `main`.
  * Tag the last commit on `main`.

GitHub Workflow automation should then prepare a deployment to Docker Hub and to `TestPyPI`.
Once the version has been published, the next deployment will then be to the official `PyPI`.

Code of Conduct
---------------

Please note that this project is released with a `Contributor Code of Conduct`_.
By participating in this project you agree to abide by its terms.

.. _`Contributor Code of Conduct`: CODE_OF_CONDUCT.rst
