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

## Release process

Create a git version tag, for example `v0.7.0`. You must make this first because the conda package uses the tag as its version.

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

Create a new release on the [releases page](https://github.com/ess-dmsc/nexus-streamer-python/releases). Add contents of [changes.md](changes.md) to the release notes.

Commit a change to bump the version number in [setup.cfg](setup.cfg) and clean [changes.md](changes.md). 
