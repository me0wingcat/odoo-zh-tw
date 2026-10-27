# odoo-zh-tw

Company-owned Traditional Chinese (zh_TW) wording for Odoo 20, kept **outside**
Odoo itself so it survives image updates and language reloads.

Odoo's own zh_TW files are never edited. This repo only holds the strings you
add or reword, and Odoo layers them on top of its own.

## How Odoo reads translations (why there are two outputs)

| String type | Examples | Where Odoo reads it | Output of `build.py` |
| --- | --- | --- | --- |
| Database (`model`, `model_terms`) | menus, field labels, help text, view text, selection values | database, loaded from every installed module's `.po` | `zh_tw_overrides/` add-on |
| Code (`odoo-python`, `odoo-javascript`) | buttons, dialogs, warnings, list headers built in JS | only the module's **own** folder: `i18n/` then `i18n_extra/` | `code_overlays/<module>/i18n_extra/` |

Code strings cannot be changed in the app or from another add-on, so they are
mounted into the module's folder as an `i18n_extra` file. Upstream ships no
`i18n_extra` for these modules, and Odoo reads it after `i18n/`, so your entries
win and everything else falls back to Odoo's.

## Layout

```
modules.txt              modules to track (edit to match what you install)
terms/<module>.po        THE file you edit (Poedit or any PO editor)
scripts/sync.py          refresh terms/ against an Odoo checkout
scripts/build.py         turn finished terms into the two outputs below
zh_tw_overrides/         generated add-on (database strings)
code_overlays/           generated i18n_extra files (code strings)
docker-compose.snippet.yml   generated volume lines for the NAS
```

`terms/<module>.po` starts with every string Odoo 20 still leaves untranslated.
Only entries that are **translated and not fuzzy** are built. Fuzzy entries are
suggestions or rewording candidates; clear the fuzzy flag once you're happy.

## Everyday workflow

1. Translate or reword entries in `terms/*.po`.
2. Run `python3 scripts/build.py`, commit, push.
3. On the NAS: `git pull` in `/volume1/docker/odoo/odoo-zh-tw`.
4. Apply (see below). Try it on the `test` database first.

To reword a string Odoo already translates (e.g. your term for 倉庫):

```bash
python3 scripts/sync.py --odoo ../odoo-src --include '倉庫|Warehouse'
```

Matching entries are copied in as fuzzy with Odoo's current wording; edit them
and clear fuzzy.

## First-time setup on the Synology

1. SSH in and clone next to your compose file:
   ```bash
   cd /volume1/docker/odoo
   git clone https://github.com/<you>/odoo-zh-tw.git
   ```
2. Confirm the addons path in your image (the overlay mounts depend on it):
   ```bash
   docker exec odoo-web python3 -c "import odoo.addons.stock as m; print(m.__path__)"
   ```
   It should print `/usr/lib/python3/dist-packages/odoo/addons/stock`. If not,
   change `IMAGE_ADDONS` in `scripts/build.py` and rebuild.
3. Merge the lines from `docker-compose.snippet.yml` into the `web` service
   volumes, and add `/mnt/zh-tw-addons` to `addons_path` in `odoo.conf`:
   ```ini
   addons_path = /mnt/extra-addons,/mnt/zh-tw-addons
   ```
4. Container Manager > Project `odoo` > Action > Build (recreates the container).
5. Apps > Update Apps List, then install **zh_TW translation overrides**.

## Applying changes

- **Code strings changed** (new or edited `code_overlays`): if you added a module
  folder, update the compose volumes and rebuild the project; otherwise just
  restart `odoo-web`. Then hard-refresh the browser (Ctrl+Shift+R).
- **Database strings changed**: Settings > Languages > 繁體中文 > Update, with
  **Overwrite Existing Terms** ticked. Modules load in dependency order, so this
  add-on's terms are applied last.

Overwrite resets any wording edited only in the app back to the files. Make
every keeper change here, in `terms/`, not just in the app.

## Keeping up with Odoo

Odoo's translators are still filling in 20.0. Run `sync.py` monthly (the GitHub
Action in `.github/workflows/sync.yml` does it and opens a PR): entries you left
empty that Odoo has since translated are removed, your own wording is kept, and
strings Odoo deleted become obsolete.

To run it locally you need an Odoo checkout with just the translation files:

```bash
git clone --depth 1 --filter=blob:none --no-checkout -b 20.0 https://github.com/odoo/odoo.git ../odoo-src
cd ../odoo-src && git sparse-checkout set --no-cone '/addons/*/i18n/zh_TW.po' '/addons/*/i18n/*.pot' \
  '/odoo/addons/base/i18n/zh_TW.po' '/odoo/addons/base/i18n/base.pot' && git checkout 20.0 && cd -
pip install polib
python3 scripts/sync.py --odoo ../odoo-src
```

Fixes that would help everyone are better sent upstream at translate.odoo.com,
so they arrive with normal Odoo updates and leave this repo.

## Major upgrade (20 → 21)

Change the branch in the workflow and the version in `scripts/build.py`, run
`sync.py` against the new branch, rebuild, and test on `test` before `prod`.
