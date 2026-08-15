# Package Version Metadata Fix

Date: 2026-08-15 UTC

## Observation

The baseline implementation, module, notebook, and handoff records identified
the current package as `0.8.0`, but `pyproject.toml` still declared distribution
version `0.7.2`. A Colab install could therefore report a different
distribution version from `tradingbot_data.__version__` even though the module
code was current.

## Correction

Commit `8aadeee328da5361736a3a09071331d761259091` changes the distribution metadata
to `0.8.0` and adds a regression test requiring the project metadata version to
equal the module version. The stateless notebook is repinned to that commit and
its package gate checks both identities.

## Local Verification

- All 26 focused tests passed.
- Python compilation completed without error.
- The wheel built as `tradingbot_data-0.8.0-py3-none-any.whl`.
- An isolated installation reported distribution version `0.8.0` and module
  version `0.8.0`.
- The installed CLI exposed the `proxy-baseline` command.

The optional training dependencies were not installed in the local verification
environment. Their installation and the first baseline run remain the pinned
Colab checkpoint.
