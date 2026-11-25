# Sunbeam libraries

Each library lives under `packages/` and has its own project metadata, version,
tests, wheel, and source distribution. The uv workspace shares a development
lockfile, and each package can be installed independently.

| Package | Import | Tested Python versions |
| --- | --- | --- |
| [sunbeam-ndr-contract](packages/ndr-contract/) | `sunbeam_ndr_contract` | 3.12 and 3.14 |

## Development

Run the tests for a single package from the repository root. Use the same
command with `--python 3.14` to check the other supported interpreter.

```sh
uv run --locked --python 3.12 --package sunbeam-ndr-contract \
    python -m pytest packages/ndr-contract/tests
```

Build the wheel and source distribution for that package independently.

```sh
uv build --package sunbeam-ndr-contract --no-sources --out-dir dist/ndr-contract
```

CI tests the installed wheel on both Python versions and stores the build
artifacts by package and Python version. Package versions are independent of
wire contract versions.

## Versioning

Each package uses `YEAR.CYCLE.PATCH` for the Sunbeam release line it
supports. A package can ship a compatible update independently by
incrementing its patch number. Use package-specific tags of the form
`<package-directory>/v<version>`.

For `sunbeam-ndr-contract`, development starts at `2027.1.0.dev0` for
the April 2027 release. The final version is `2027.1.0`, followed by
compatible updates such as `2027.1.1`. When work on the next release line
starts in May, use `2027.2.0.dev0` for that work. The NDR wire contract
version is maintained separately.

### Release a beta

Set the package version to `2027.1.0b1` and build its wheel and source
distribution. `uv version` updates the package metadata and workspace lockfile.

```sh
uv version --package sunbeam-ndr-contract --no-sync 2027.1.0b1
uv lock --check
uv build --package sunbeam-ndr-contract --no-sources \
    --out-dir dist/ndr-contract/2027.1.0b1
```

Commit the version and lockfile changes. After the Python 3.12 and 3.14
checks pass, create a signed tag on the release commit and push that tag
to the canonical repository.

```sh
git tag -s ndr-contract/v2027.1.0b1 -m "NDR contract 2027.1.0b1"
git push origin refs/tags/ndr-contract/v2027.1.0b1
```

The [release workflow](.github/workflows/release.yaml) checks the tag
against the package version, builds the distributions, and tests them
on both Python versions. The publish job uploads those artifacts to
PyPI through the `pypi-ndr-contract` GitHub environment.

Configure PyPI Trusted Publishing for `canonical/sunbeam-libs` with
workflow filename `release.yaml` and environment `pypi-ndr-contract`.
The GitHub environment must allow `ndr-contract/v*` release tags.
Consumers can opt into the published beta with the exact requirement
`sunbeam-ndr-contract==2027.1.0b1`.

For another beta use `2027.1.0b2`. For the final release use `2027.1.0`
and follow the same build and tag steps.

### Publish a development release

If the package metadata already reads `2027.1.0.dev0`, tag the commit containing
the package version and release workflow, then push that tag.

```sh
git tag -s ndr-contract/v2027.1.0.dev0 -m "NDR contract 2027.1.0.dev0"
git push origin refs/tags/ndr-contract/v2027.1.0.dev0
```

The release workflow builds, tests, and publishes the development version.
Consumers can opt in with `sunbeam-ndr-contract==2027.1.0.dev0`. Use
`2027.1.0.dev1` for the next development upload.
