#!/usr/bin/env python3

import argparse

from generate_subscriptions import generate_all_subscriptions
from import_configs import rebuild_database
from user_ops import DEFAULT_CATALOGUE, collect_reality_configs, save_config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Delete a VLESS Reality client from all existing Reality server configs."
    )
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--email")
    selector.add_argument("--id", dest="client_id")
    parser.add_argument("--catalogue", default=str(DEFAULT_CATALOGUE))
    parser.add_argument("--dbpath", default="subscriptions.db")
    parser.add_argument("--outdir", default="subscriptions")
    parser.add_argument("--domain", default="fp.work.gd")
    parser.add_argument("--encryption", default="none")
    parser.add_argument("--headertype", default="none")
    parser.add_argument("--fingerprint", default="chrome")
    return parser.parse_args()


def matches(client, args):
    if args.email is not None:
        return client.get("email") == args.email
    return client.get("id") == args.client_id


def main():
    args = parse_args()
    entries = collect_reality_configs(args.catalogue)

    if not entries:
        raise SystemExit("No VLESS Reality server configs found.")

    changed_files = []
    removed_clients = []

    for entry in entries:
        file_changed = False
        for inbound in entry["inbounds"]:
            clients = inbound.get("settings", {}).get("clients", [])
            kept_clients = []
            inbound_changed = False

            for client in clients:
                if matches(client, args):
                    removed_clients.append(
                        (entry["host"], inbound.get("tag", "untagged"), client.get("id"), client.get("email"))
                    )
                    inbound_changed = True
                    continue
                kept_clients.append(client)

            if inbound_changed:
                file_changed = True
                inbound["settings"]["clients"] = kept_clients

        if file_changed:
            save_config(entry["path"], entry["config"])
            changed_files.append(entry["path"])

    if not removed_clients:
        target = args.email if args.email is not None else args.client_id
        raise SystemExit(f"No matching client found for {target}")

    rebuild_database(
        args.catalogue,
        args.dbpath,
        domain=args.domain,
        encryption=args.encryption,
        headertype=args.headertype,
        fingerprint=args.fingerprint,
    )
    generate_all_subscriptions(args.dbpath, args.outdir)

    print(f"Removed {len(removed_clients)} client binding(s).")
    print("Updated config files:")
    for changed_file in changed_files:
        print(f"- {changed_file}")


if __name__ == "__main__":
    main()
