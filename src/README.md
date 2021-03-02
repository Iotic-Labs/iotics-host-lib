iotics.host.lib.sources
=======================

Iotics QAPI common sources.


Debug helper
------------

\*\***This is not for unit test purpose**\*\*


If you want to try your code against a real host you will need a set of identities.
The following helper provides agent and user identities with delegation. Those can be used to
instantiate the [AgentAuthBuilder](./iotics/host/auth.py) which is a parameter of the [QApiFactory](./iotics/host/api/qapi.py)

Run:
```shell script
RESOLVER=http://localhost:5000 python get_debug_auth.py 
```
Output example:
```shell script
DEBUG identities:
SEED: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
USER: did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM#user-0
```

Authentication helper instantiation example:

```python
AgentAuthBuilder.build_agent_auth("http://localhost:5000",
                                  "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                                  "did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM#user-0",
                                  method=SeedMethod.SEED_METHOD_BIP39)
```
