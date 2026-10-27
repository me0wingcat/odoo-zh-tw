#!/usr/bin/env python3
"""Refresh terms/<module>.po against an odoo/odoo checkout.

For each module listed in modules.txt:
  * adds every string Odoo's own zh_TW file still leaves untranslated (empty msgstr);
  * keeps everything you already translated or reworded;
  * drops empty entries that upstream has since translated (nothing left to do);
  * marks entries obsolete when the string no longer exists in Odoo.

Options:
  --previous PATH   an older odoo checkout (e.g. 19.0); its translation of an
                    identical string is pre-filled as a *fuzzy* suggestion.
  --include REGEX   also copy already-translated upstream strings whose source
                    or translation matches REGEX, marked fuzzy, so you can
                    reword them (e.g. --include '倉庫|Warehouse').

Usage:
  python3 scripts/sync.py --odoo ../odoo-src [--previous ../odoo-19] [--include REGEX]
"""
import argparse
import os
import re
import sys

import polib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LANG, i18n_dir, is_translated, key, copy_entry, new_po  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    return polib.pofile(path, wrapwidth=0) if os.path.exists(path) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--odoo", required=True)
    ap.add_argument("--previous")
    ap.add_argument("--include")
    ap.add_argument("--modules", default=os.path.join(ROOT, "modules.txt"))
    args = ap.parse_args()
    rx = re.compile(args.include) if args.include else None

    modules = [m.strip() for m in open(args.modules, encoding="utf-8") if m.strip() and not m.startswith("#")]
    total_todo = total_mine = 0
    for mod in modules:
        d = i18n_dir(args.odoo, mod)
        pot = load(os.path.join(d, f"{mod}.pot"))
        if pot is None:
            print(f"! {mod}: no {mod}.pot in {d}, skipped")
            continue
        upstream = load(os.path.join(d, f"{LANG}.po"))
        up = {key(e): e for e in upstream if not e.obsolete} if upstream else {}
        prev = {}
        if args.previous:
            p = load(os.path.join(i18n_dir(args.previous, mod), f"{LANG}.po"))
            if p:
                prev = {key(e): e for e in p if is_translated(e)}

        path = os.path.join(ROOT, "terms", f"{mod}.po")
        old = load(path)
        mine = {key(e): e for e in old if not e.obsolete} if old else {}

        out = new_po()
        todo = owned = 0
        for src in pot:
            if src.obsolete:
                continue
            k = key(src)
            u = up.get(k)
            m = mine.get(k)
            stale_suggestion = (m is not None and "fuzzy" in m.flags
                                and m.tcomment == "suggestion from previous Odoo version"
                                and u is not None and is_translated(u))
            if m is not None and not stale_suggestion and (is_translated(m) or "fuzzy" in m.flags):
                # yours: keep your wording, refresh references from the current pot
                e = copy_entry(src, msgstr=m.msgstr, msgstr_plural=m.msgstr_plural,
                               flags=[f for f in m.flags if f == "fuzzy"])
                e.tcomment = m.tcomment
                out.append(e)
                owned += 1
            elif u is None or not is_translated(u):
                e = copy_entry(src, msgstr="", msgstr_plural={0: ""} if src.msgid_plural else {}, flags=[])
                pv = prev.get(k)
                if pv is not None:
                    e.msgstr, e.msgstr_plural = pv.msgstr, dict(pv.msgstr_plural)
                    e.flags = ["fuzzy"]
                    e.tcomment = "suggestion from previous Odoo version"
                out.append(e)
                todo += 1
            elif rx and (rx.search(src.msgid) or rx.search(u.msgstr or "")):
                out.append(copy_entry(src, msgstr=u.msgstr, msgstr_plural=u.msgstr_plural, flags=["fuzzy"]))
                owned += 1
        # keep removed strings you had translated, as obsolete history
        live = {key(e) for e in pot if not e.obsolete}
        for k, m in mine.items():
            if k not in live and is_translated(m):
                m.obsolete = True
                out.append(m)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.save(path)
        total_todo += todo
        total_mine += owned
        print(f"{mod:18} untranslated upstream: {todo:5}   yours/reviewing: {owned:5}")
    print(f"{'TOTAL':18} untranslated upstream: {total_todo:5}   yours/reviewing: {total_mine:5}")


if __name__ == "__main__":
    main()
