# Developer documentation

Adding or removing dependencies must be done in both [conda/meta.yaml](conda/meta.yaml) and [setup.cfg](setup.cfg).

## Development dependencies

In addition to the dependencies listed in setup.cfg there are some development dependencies.
These can be installed using pip

```commandline
pip install -r requirements-dev.txt
```

`black`, `flake8` and `mypy` can be used as a pre-commit hook (installed by [pre-commit](https://pre-commit.com/)).
You need to run
```commandline
pre-commit install
```
once to activate the pre-commit check.
To test the hooks run
```commandline
pre-commit run --all-files
```
This command can also be used to run the hooks manually.

## Run from source

[src/run_nexus_streamer.py](src/run_nexus_streamer.py) can be used to run the application from source.
For example
```commandline
python src/run_nexus_streamer.py --help
```

## Release process

Commit a change to bump the version number in [src/nexus_streamer/__init__.py](src/nexus_streamer/__init__.py).
Create a git version tag, for example `v0.7.0`. You must make this first because the conda package uses the tag as its version.

### 1. Create conda package

You must have a conda installation, for example `conda` via pip, or [miniconda](https://docs.conda.io/en/latest/miniconda.html).

From the directory of the nexus-streamer-python repository, build the package with
```commandline
conda install -c conda-forge conda-build anaconda-client
conda build -c conda-forge ./conda
```

To upload the package, first login
```commandline
anaconda login
```
use the ESS-DMSC-ECDC account or personal account linked to ESS-DMSC organisation.

Find the path for the built package using
```commandline
conda build ./conda --output
```

Then upload
```commandline
anaconda upload --user ESS-DMSC /path/to/package
```

### 2. Create pypi package

Uninstall streaming_data_types if you have previous installed it from PyPi
```commandline
pip uninstall ess_streaming_data_types
```

Delete any old builds you may have (IMPORTANT!)
```commandline
rm -rf build dist
```

Build it locally
```commandline
python setup.py sdist bdist_wheel
```

Push to PyPI
```commandline
twine upload dist/*
```
and login with the ESS-DMSC-ECDC PyPi account. 

### 3. Create release on github

Create a new release on the [releases page](https://github.com/ess-dmsc/nexus-streamer-python/releases). Add contents of [changes.md](changes.md) to the release notes.

Clean [changes.md](changes.md). 
