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
