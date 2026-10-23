"""cli.py — `goldenreq list | accept | reject` (argparse, stdlib only)."""
from __future__ import annotations

import argparse
import json
import sys

from .queue import list_pending
from .verdict import accept, reject


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="goldenreq",
                                description="the acceptance gate for goldenization — nothing self-promotes")
    p.add_argument("--queue", default=None, help="queue JSONL path ($GOLDENREQ_QUEUE_PATH)")
    sub = p.add_subparsers(dest="cmd", required=True)

    lp = sub.add_parser("list", help="list pending requests (the handler's inbox)")
    lp.add_argument("--json", action="store_true", help="emit raw JSON lines")

    ap = sub.add_parser("accept", help="accept a request → fire its promotion effect")
    ap.add_argument("request_id")
    ap.add_argument("--by", required=True, help="ruling actor (human:<who> / model:<id>)")
    ap.add_argument("--reason", default="")

    rp = sub.add_parser("reject", help="reject a request (reason = hard negative)")
    rp.add_argument("request_id")
    rp.add_argument("--by", required=True, help="ruling actor (human:<who> / model:<id>)")
    rp.add_argument("--reason", required=True)

    args = p.parse_args(argv)

    if args.cmd == "list":
        pending = list_pending(args.queue)
        if args.json:
            for r in pending:
                print(json.dumps(r, sort_keys=True))
        elif not pending:
            print("no pending requests")
        else:
            for r in pending:
                print(f"{r['request_id']}  {r['kind']:<16}  {r['candidate_id']}  "
                      f"→ {r['requested_promotion']}  (by {r['requester']}, "
                      f"{len(r.get('evidence', []))} receipt(s))")
        return 0

    try:
        if args.cmd == "accept":
            v = accept(args.request_id, args.by, args.reason, queue_path=args.queue)
        else:
            v = reject(args.request_id, args.by, args.reason, queue_path=args.queue)
    except (ValueError, FileNotFoundError, NotImplementedError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(v, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
