# NeXus Streamer

This is intended to replace https://github.com/ess-dmsc/NeXus-Streamer with a Python implementation which should be much lower effort to maintain. The C++ implmentation is not yet obsolete, missing features in this implementation are documented in tickets.

## Installing dependencies

Python 3.7 or higher is required. https://www.python.org/downloads/

Runtime Python dependencies are listed in `requirements.txt` at the root of the
repository. They can be installed from a terminal by running
```
pip install -r requirements.txt
```

## Developer information

### Development dependencies

Development dependencies (including all runtime dependencies) can be installed by using the following command

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
