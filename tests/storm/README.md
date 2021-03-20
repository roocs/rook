# Run locaust tests

## Install

Install locust requirements:
```
pip install -r tests/storm/requirements.txt
```

## Run

Run:
```
locust -f tests/storm/locustfile.py
```

And select the rook server to test in the web interface:
http://0.0.0.0:8089

### Using tags

You can use tags to run specific tests:
```
locust -f tests/storm/locustfile.py --tags subset
```

Or exclude tags:
```
locust -f tests/storm/locustfile.py --exclude-tags meta
```

Existing tags:
* `meta`,
* `subset`,
* `average`,
* `workflow`

See:
* https://docs.locust.io/en/stable/writing-a-locustfile.html#tag-decorator


## Links

* https://locust.io/
* https://github.com/pglass/how-do-i-locust
