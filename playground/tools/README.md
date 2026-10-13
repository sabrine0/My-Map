# Tools

- `make_skins.py` — generates every skin in `../skins/` (themes, Moroccan
  cities, 250 countries) plus the flat copies in `../../styles/` for the Docker
  tile server. Edit the palettes at the top of the file, then:

      python make_skins.py

- `country_palettes.py` — rebuilds `countries_palette.json` (flag colours and
  capital coordinates) from `mledoze/countries` and Natural Earth. Only needed
  if you want to refresh that data; it downloads flag images into `flags/`.
- `sprite.json` — index of the OpenFreeMap sprite, used to know which POI
  classes have an icon.
- `thumbs.js` — renders the gallery thumbnails into `../thumbs/` with headless
  Edge (needs `npm install puppeteer-core` next to it and the playground
  server running on port 3030). `FORCE=1 node thumbs.js` redraws all.

## watermarks-remover

`watermarks-remover/` is a clone of
[guillaumemeyer/watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover)
(MIT). It strips provenance and AI metadata (C2PA, EXIF, XMP, PNG text
chunks, document properties) from files, and invisible Unicode from text.
Python only, nothing to install; `exiftool` and `c2patool` are optional extras
it will use if present on the PATH.

How the playground uses it:

- `serve.py` exposes `POST /clean`. The **PNG** and **Export JSON** buttons
  send their file through it before the download, so nothing you save from
  the playground carries metadata. The status line says "metadata stripped"
  or "clean".
- Check one file by hand:

      python tools/watermarks-remover/service/scripts/inspect_file.py --json thumbs/casablanca.png
      python tools/watermarks-remover/service/scripts/clean_file.py some.png -o some.clean.png

- Audit the whole playground folder:

      python tools/watermarks-remover/service/scripts/audit_dir.py .

To update it: `git -C tools/watermarks-remover pull`.
