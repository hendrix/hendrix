## Running the test suite

In your virtualenv first run the following:

pip install -r requirements
pip install -r test-requirements

Tests live in `hendrix.test` and are most easily run using Twisted's
[trial](https://twistedmatrix.com/trac/wiki/TwistedTrial) test framework.
```bash
/home/jsmith:~$ trial hendrix
hendrix.test.test_deploy
DeployTests
test_multiprocessing ...                                               [OK]
test_options_structure ...                                             [OK]
test_settings_doesnt_break ...                                         [OK]

-------------------------------------------------------------------------------
Ran 3 tests in 0.049s

PASSED (successes=3)
```
**trial** will find your tests so long as you name the package/module such that
it starts with "test" e.g. `hendrix/contrib/cache/test/test_services.py`.

Note that the module needs to have a subclass of unittest.TestCase via the expected
unittest pattern. For more info on *trial* go [here](https://twistedmatrix.com/trac/wiki/TwistedTrial).

N.B. that in the `hendrix.test` `__init__.py` file a subclass of TestCase
called `HendrixTestCase` has been created to help tests various use cases
of `hendrix.deploy.HendrixDeploy`
