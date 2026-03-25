# Xray Subscription Builder

Utility scripts for building VLESS Reality subscription files from Xray server configs.

## Purpose

This directory contains a small offline workflow:

1. Validate Xray server configs in `../configs`.
2. Import the relevant server and client data into `subscriptions.db`.
3. Generate per-client subscription files under `subscriptions/`.
4. Optionally append bypass variants that replace the original endpoint host and port.

The tools are intended for VLESS Reality server configs. Hosts that do not expose a VLESS Reality inbound are ignored during import and reported as informational during validation.

## Scope

This project covers only:

- validating existing Xray server configs
- importing the required data into SQLite
- generating client subscription files
- appending optional bypass variants

Out of scope:

- managing or provisioning Xray server configurations
- deploying, serving, or distributing the generated subscription files

## Files

- `validate_configs.py`: validates config structure and required metadata before import.
- `import_configs.py`: rebuilds the SQLite database from the config catalogue.
- `generate_subscriptions.py`: generates plain-text and base64 subscriptions for each client.
- `create_bypass.py`: interactively appends bypass endpoint variants to every client subscription.
- `Makefile`: wraps the common workflow.

## Expected Layout

The importer expects host directories like:

```text
../configs/<host>/
├── config.json
├── key.pub
└── country.txt
```

- `config.json` is the Xray config for that host.
- `key.pub` is required for any host with a VLESS Reality inbound because it is used as `pbk` in generated URLs.
- `country.txt` is optional. It is used only as a label fragment in generated URL names.

## What Gets Imported

For each inbound that matches:

- `protocol == "vless"`
- `streamSettings.security == "reality"`

the importer stores:

- host name and public domain
- inbound tag, protocol, network, security, port
- Reality settings needed for client URLs
- client UUID, email label, and flow

The database is rebuilt from scratch on every import. Re-running the import does not duplicate rows.

## Generated Output

Subscriptions are written under:

```text
subscriptions/<uuid>/
├── <normalized-email>.txt
└── <normalized-email>.b64
```

- `.txt` contains one VLESS URL per line.
- `.b64` contains the same content base64-encoded.
- filenames are normalized from client email labels to avoid spaces and filesystem-hostile characters.

The URL label fragment still uses the original client email label, not the normalized filename.

## Quick Start

Validate, import, and generate subscriptions:

```bash
make rebuild
```

Generate subscriptions with interactive bypass variants:

```bash
make bypass
```

Syntax check the scripts:

```bash
make check
```

Remove generated artifacts:

```bash
make clean
```

## Make Targets

- `make check`: run Python syntax checks.
- `make validate`: validate the config catalogue.
- `make import`: rebuild `subscriptions.db` from configs.
- `make generate`: generate subscription files from the database.
- `make rebuild`: run `validate`, `import`, and `generate`.
- `make bypass`: run `validate`, `import`, and then append interactive bypass variants.
- `make clean`: remove `subscriptions.db` and `subscriptions/`.

## Direct Script Usage

Default paths match the current repository layout:

```bash
./validate_configs.py
./import_configs.py
./generate_subscriptions.py
./create_bypass.py
```

Custom paths can be supplied when needed:

```bash
./validate_configs.py --catalogue ../configs
./import_configs.py --catalogue ../configs --dbpath subscriptions.db
./generate_subscriptions.py --dbpath subscriptions.db --outdir subscriptions
./create_bypass.py --dbpath subscriptions.db --outdir subscriptions
```

## Validation Rules

`validate_configs.py` checks:

- JSON parsing and top-level `inbounds` structure
- presence of required Reality fields
- missing or empty `key.pub` for Reality hosts
- missing or empty `country.txt` for Reality hosts
- duplicate client UUIDs inside one inbound
- UUID reuse with different email labels across hosts

Hosts without VLESS Reality inbounds do not fail validation.

## Bypass Mode

`create_bypass.py` reads the already imported host list and prompts once per original endpoint.

For each endpoint you can:

- enter a bypass hostname
- enter an IPv4 address
- enter an IPv6 address
- skip that endpoint

Bypass behavior:

- only the endpoint host and port are replaced
- all other URL parameters stay unchanged
- bypass additions are applied for all users
- the first entered bypass host and port become the defaults for later prompts
- pressing `Enter` on later prompts reuses the remembered defaults
- entering `-` at a later host prompt skips that specific endpoint

## Notes

- `subscriptions.db` and `subscriptions/` are ignored by Git because they are generated artifacts and may contain sensitive client data.
- `make rebuild` stops immediately if validation fails.
- the tools use only the Python standard library

## Recommended Next Improvements

- Add tests with a small fixture set covering multiple hosts and multiple Reality inbounds on one host.
