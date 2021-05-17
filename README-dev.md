# Developer documentation

Adding or removing dependencies must be done in both [conda/meta.yaml](conda/meta.yaml) and [setup.cfg](setup.cfg).

## Development dependencies

In addition to the dependencies listed in setup.cfg there are some development dependencies.
These can be installed using pip

```
pip install -r requirements-dev.txt
```

`black`, `flake8` and `mypy` can be used as a pre-commit hook (installed by [pre-commit](https://pre-commit.com/)).
You need to run
```
pre-commit install
```
once to activate the pre-commit check.
To test the hooks run
```
pre-commit run --all-files
```
This command can also be used to run the hooks manually.

## Release process


