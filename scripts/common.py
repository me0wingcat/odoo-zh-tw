"""Shared helpers for the zh_TW override tooling."""
import os
import polib

LANG = "zh_TW"

HEADER = {
    "Project-Id-Version": "Odoo zh_TW overrides",
    "Language": LANG,
    "MIME-Version": "1.0",
    "Content-Type": "text/plain; charset=UTF-8",
    "Content-Transfer-Encoding": "8bit",
    "Plural-Forms": "nplurals=1; plural=0;",
}


def i18n_dir(odoo_src, module):
    """Where a module's i18n folder lives in an odoo/odoo checkout."""
    if module == "base":
        return os.path.join(odoo_src, "odoo", "addons", "base", "i18n")
    return os.path.join(odoo_src, "addons", module, "i18n")


def new_po():
    po = polib.POFile(wrapwidth=0)
    po.metadata = dict(HEADER)
    return po


def key(entry):
    return (entry.msgctxt, entry.msgid)


def is_translated(entry):
    if entry.obsolete or "fuzzy" in entry.flags:
        return False
    if entry.msgid_plural:
        return any(v for v in entry.msgstr_plural.values())
    return bool(entry.msgstr)


def kinds(entry):
    """Set of occurrence kinds: 'code', 'model', 'model_terms'."""
    return {occ.split(":", 1)[0] for occ, _ in entry.occurrences}


def copy_entry(entry, occurrences=None, msgstr=None, msgstr_plural=None, flags=None):
    e = polib.POEntry(
        msgid=entry.msgid,
        msgctxt=entry.msgctxt,
        msgid_plural=entry.msgid_plural,
        msgstr=entry.msgstr if msgstr is None else msgstr,
        msgstr_plural=dict(entry.msgstr_plural if msgstr_plural is None else msgstr_plural),
        occurrences=list(entry.occurrences if occurrences is None else occurrences),
        comment=entry.comment,  # keeps "module: x" and odoo-python / odoo-javascript markers
        tcomment=entry.tcomment,
        flags=list(entry.flags if flags is None else flags),
    )
    return e
