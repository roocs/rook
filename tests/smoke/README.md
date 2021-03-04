# Run smoke tests

Smoke tests are run on a live pywps server.
The tests are marked with `pytest.mark.smoke`.

## Run smoke tests locally

Run test-suite first (get test-data etc) ... *only* once:
```
make test
```

Export generated `roocs.ini` to be used in tests:
```
export ROOCS_CONFIG=$PWD/tests/.roocs.ini
```

Start rook service:
```
make start
```

Run smoke tests:
```
pytest -v -m "smoke" tests/

OR

make smoke
```

Stop service:
```
make stop
```

## Run against a remote pywps server

Edit url in `etc/smoke-pywps.cfg`:
```ini
[server]
url = http://rook1.cloud.dkrz.de/wps
```

Export this config:
```
export PYWPS_CFG=$PWD/etc/smoke-pywps.cfg
```

Run tests:
```
pytest -v -m "smoke" tests/

OR

make smoke
```

## Run smoke tests on a deployed pywps server

The ansible playbook for rook prepares a script to run a smoke test:
* https://github.com/bird-house/ansible-wps-playbook
* https://github.com/bird-house/ansible-wps-playbook/blob/3b65fc1e2ac755a4f2d7e4cf16e33d8ba6a12a99/roles/pywps/tasks/cronjob.yml#L75

Run the smoke test on a deployed server:
```
/var/lib/pywps/smoke.sh rook
```
