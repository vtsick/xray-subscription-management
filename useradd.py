#!/usr/bin/env python3

import argparse
import base64
import subprocess
import uuid

from generate_subscriptions import generate_all_subscriptions, normalize_filename_component
from import_configs import rebuild_database
from user_ops import DEFAULT_CATALOGUE, collect_reality_configs, save_config


DEFAULT_URL_PREFIX = "https://void.fp.work.gd:10443/xray/subscriptions"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Add a VLESS Reality client to all existing Reality server configs."
    )
    parser.add_argument("email")
    parser.add_argument("--id", dest="client_id")
    parser.add_argument("--flow", default="xtls-rprx-vision")
    parser.add_argument("--catalogue", default=str(DEFAULT_CATALOGUE))
    parser.add_argument("--dbpath", default="subscriptions.db")
    parser.add_argument("--outdir", default="subscriptions")
    parser.add_argument("--url-prefix", default=DEFAULT_URL_PREFIX)
    parser.add_argument("--domain", default="fp.work.gd")
    parser.add_argument("--encryption", default="none")
    parser.add_argument("--headertype", default="none")
    parser.add_argument("--fingerprint", default="chrome")
    return parser.parse_args()


def render_qr(text):
    try:
        completed = subprocess.run(
            ["qrencode", "-t", "ANSIUTF8", text],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("qrencode is required for QR output but was not found in PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"qrencode failed: {exc.stderr.strip()}") from exc
    return completed.stdout.rstrip()


def main():
    args = parse_args()
    client_id = args.client_id or str(uuid.uuid4())
    entries = collect_reality_configs(args.catalogue)

    if not entries:
        raise SystemExit("No VLESS Reality server configs found.")

    changed_files = []
    updated_inbounds = 0

    for entry in entries:
        file_changed = False
        for inbound in entry["inbounds"]:
            clients = inbound.setdefault("settings", {}).setdefault("clients", [])

            match = None
            for client in clients:
                if client.get("id") == client_id and client.get("email") == args.email:
                    match = client
                    break
                if client.get("email") == args.email and client.get("id") != client_id:
                    raise SystemExit(
                        f"Email {args.email} already exists with a different id in {entry['host']}"
                    )
                if client.get("id") == client_id and client.get("email") != args.email:
                    raise SystemExit(
                        f"ID {client_id} already exists with a different email in {entry['host']}"
                    )

            if match:
                if match.get("flow") != args.flow:
                    match["flow"] = args.flow
                    file_changed = True
                updated_inbounds += 1
                continue

            clients.append(
                {
                    "id": client_id,
                    "email": args.email,
                    "flow": args.flow,
                }
            )
            file_changed = True
            updated_inbounds += 1

        if file_changed:
            save_config(entry["path"], entry["config"])
            changed_files.append(entry["path"])

    rebuild_database(
        args.catalogue,
        args.dbpath,
        domain=args.domain,
        encryption=args.encryption,
        headertype=args.headertype,
        fingerprint=args.fingerprint,
    )
    generate_all_subscriptions(args.dbpath, args.outdir)

    filename = f"{normalize_filename_component(args.email)}.b64"
    subscription_path = f"{client_id}/{filename}"
    subscription_url = f"{args.url_prefix.rstrip('/')}/{subscription_path}"
    encoded_url = base64.b64encode(subscription_url.encode("utf-8")).decode("ascii")
    qr_text = render_qr(subscription_url)

    print(f"Added client to {updated_inbounds} reality inbound(s).")
    if changed_files:
        print("Updated config files:")
        for changed_file in changed_files:
            print(f"- {changed_file}")
    else:
        print("Client already existed everywhere. Subscriptions were regenerated.")

    print()
    print(f"ID: {client_id}")
    print(f"Email: {args.email}")
    print(f"Subscription path: {subscription_path}")
    print(f"Subscription URL: {subscription_url}")
    print(f"Subscription URL (base64): {encoded_url}")
    print("Subscription URL QR (ANSI UTF-8):")
    print(qr_text)


if __name__ == "__main__":
    main()
