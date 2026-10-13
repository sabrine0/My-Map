# Building your own map style

You write `style.json`. The browser redraws the map within a second of every
save. No Docker, no tile build: the OpenStreetMap data comes as vector tiles
from OpenFreeMap (free, no key), and *you* decide how every piece is drawn.

## Start

    python serve.py

Open http://localhost:3030. Open `style.json` in your editor next to it.
Change `"background-color"` to `"#000000"`, save, watch the map go black.
That loop is the whole workflow.

## The viewer's tools

Top row: **Find** filters the skin list (`/`), the dropdown picks a skin,
**Gallery** (`g`) shows every skin as a picture.

Second row: **Go to city**, a **place search** (any address or landmark,
via OpenStreetMap's Nominatim, Enter to fly there), **Labels** FR / AR / EN /
local (`l` cycles; it rewrites every label layer's `text-field`), **3D**
(`3`), **Globe**, **Orbit** (`o`, a slow circling camera; any drag stops it),
**Inspect data** (`i`), **Tweak** (`t`), **PNG** (`s`, saves the view as an
image), **Link** (`c`, copies a link to this exact view and skin), **?**.

Bottom: the position read-out and the **sun slider**: time of day moves the
light that shades buildings and relief, and dims the map into night. It is a
viewer effect only; skin files do not change.

Third row, the map tools:

- **Route** (`d`): click a start and an end; the route is drawn with its
  distance, time and turn-by-turn steps, alternatives dashed. Drag the pins
  to re-route, Swap reverses. Routing by the public OSRM demo server
  (driving profile, fair use). Needs internet.
- **Measure** (`m`): click points, double-click or Esc to finish; the total
  distance follows the last point.
- **Satellite** (`x`): aerial imagery under the skin's roads, buildings and
  labels, with an opacity slider. Works on any skin.
- **Rain**: live rain radar from RainViewer, refreshed every five minutes.
- **Bookmarks** (`b` saves): named views that remember skin and camera.
  They live in this browser's local storage.
- **Tour**: flies through the fifteen Moroccan city skins, pausing to orbit
  each one. Esc stops it.

Route, measure, satellite and rain all survive a skin change.

**Saved files are cleaned.** The PNG and Export JSON buttons pass the file
through `tools/watermarks-remover` (MIT) on the way out, which strips
provenance and AI metadata. See `tools/README.md` for the command-line use.

**Tweak** is the quickest way to learn: it lists the main colours of the
current skin (ground, water, parks, forest, buildings, roads, rail, borders,
text) plus relief and building-height multipliers. Drag a colour and the map
updates instantly. **Export JSON** downloads the result as a full style you
can drop into `skins/` (and add to `skins.json`); **Reset** returns to the
file on disk. Keyboard: `n` / `p` next and previous skin, `r` random.

## How a style works

A style has three parts:

1. **sources** – where the data comes from. One vector source here, called `osm`.
2. **glyphs / sprite** – fonts for labels and icons.
3. **layers** – an ordered list. Each layer picks *some* data and says *how*
   to draw it. First layer is drawn first, so it ends up at the bottom.

A layer always has:

| key            | meaning                                                     |
|----------------|-------------------------------------------------------------|
| `id`           | any unique name, for you                                    |
| `type`         | `background`, `fill` (areas), `line`, `symbol` (text/icons), `circle` |
| `source`       | `osm`                                                       |
| `source-layer` | which table inside the tiles (see list below)               |
| `filter`       | optional: keep only some features of that table             |
| `paint`        | colours, widths, opacity                                    |
| `layout`       | text content, fonts, line caps, visibility                  |
| `minzoom` / `maxzoom` | only draw between these zooms                        |

Filters read the feature's tags. Common forms:

    ["==", "class", "city"]
    ["in", "class", "motorway", "trunk", "primary"]
    ["!=", "intermittent", 1]
    ["all", ["==", "class", "river"], [">=", "zoom", 8]]

Anything can vary with zoom using `interpolate`:

    ["interpolate", ["linear"], ["zoom"],  5, 0.5,  10, 2,  14, 6]
    // at zoom 5 → 0.5, zoom 10 → 2, zoom 14 → 6, smooth in between

## What is in the tiles

The data follows the OpenMapTiles schema. `source-layer` → useful tags:

| source-layer          | geometry | main tags                                                  |
|-----------------------|----------|------------------------------------------------------------|
| `water`               | polygon  | `class`: ocean, lake, river; `intermittent`                |
| `waterway`            | line     | `class`: river, stream, canal; `name`                      |
| `landcover`           | polygon  | `class`: wood, grass, sand, ice, wetland, farmland         |
| `landuse`             | polygon  | `class`: residential, commercial, industrial, cemetery…    |
| `park`                | polygon  | `class`: park, national_park, nature_reserve               |
| `building`            | polygon  | `render_height`, `render_min_height`                       |
| `transportation`      | line     | `class`: motorway, trunk, primary, secondary, tertiary, minor, service, path, rail; `brunnel`: bridge/tunnel; `ramp` |
| `transportation_name` | line     | same classes + `name`, `ref` (road number)                 |
| `boundary`            | line     | `admin_level` (2 = country, 4 = region); `disputed`; `maritime` |
| `place`               | point    | `class`: country, state, city, town, village, suburb; `rank`; `name`, `name:fr`, `name:ar`, `name:en` |
| `water_name`          | point/line | lake and sea names                                       |
| `poi`                 | point    | `class`, `subclass`, `name`, `rank`                        |
| `aeroway`             | poly/line| runways, taxiways                                          |
| `mountain_peak`       | point    | `ele` (elevation), `name`                                  |
| `housenumber`         | point    | `housenumber`                                              |

Press **Inspect data** in the page to see every table drawn in a different
colour. **Click** anything to read its real tags. Full reference:
https://openmaptiles.org/schema/

## Exercises, in order

Each one is a few lines. Save after each and look.

1. **Parks.** Add a `fill` layer on `park`, colour `#c8e6c9`. Put it right
   after `background`, before `water`, so lakes still show on top.
2. **Minor roads.** Copy `road-major`, rename it `road-minor`, filter
   `["in", "class", "secondary", "tertiary", "minor"]`, thinner and grey,
   `"minzoom": 9`. Place it *before* `road-major` so big roads draw on top.
3. **Road casing.** Add a second line layer for major roads just before
   `road-major` with the same filter, darker colour, and width + 2. That is
   how outlined roads are made: two layers.
4. **Buildings.** `fill` on `building`, `"minzoom": 13`, colour `#d9d0c1`.
5. **Towns.** Copy `place-city` → `place-town`, filter `class == town`,
   smaller text, `Noto Sans Regular`, `"minzoom": 7`.
6. **Country border.** `line` on `boundary`,
   filter `["all", ["==", "admin_level", 2], ["!=", "disputed", 1], ["!=", "maritime", 1]]`,
   dashed: `"line-dasharray": [4, 2]`.
7. **Road names.** `symbol` on `transportation_name`, `"symbol-placement": "line"`,
   `"text-field": ["get", "name"]`, `"minzoom": 12`.
8. **Arabic labels.** Change `text-field` to prefer `name:ar`. Try
   `"text-font": ["Noto Sans Regular"]` which has Arabic glyphs.
9. **Rivers.** `line` on `waterway`, width growing with zoom, same blue as water.
10. **Night mode.** Change every colour. Save as `style-dark.json` and switch
    the `fetch('style.json…')` line in `index.html`.

## What every skin draws

All generated skins share one layer list (58 layers), so learn it once:

- **Ground**: residential, commercial and industrial land; farmland, sand,
  rock, ice, grass, wood, wetland; hospitals/schools/universities, cemeteries,
  sports pitches, parks (with an outline when zoomed in); airports with runways
  and taxiways; shaded relief.
- **Water**: lakes and sea with a thin shoreline, rivers and canals wider than
  streams, river names along the line.
- **Buildings**: 3D, lit from the top-left (`light` root property), and
  colour-graded by height (taller is lighter, or darker on pale skins).
- **Roads**: tunnels dashed and faded underneath; footpaths dashed; service
  lanes thin; minor and major roads with casings; highways on top; one-way
  arrows at street level (light skins); rails with sleepers; trams and metro
  dashed. `line-sort-key` on the `layer` tag puts bridges above underpasses.
- **Labels**: house numbers (z17+), street names, highway number shields,
  POI icons on white discs with names (important ones from z14, the rest from
  z16, only classes the sprite has an icon for), peaks with height, villages,
  towns and cities (with a dot when zoomed out, capitals bigger), regions,
  countries.

Per-skin colour keys beyond the basics are optional: `wood`, `grass`,
`wetland`, `civic`, `pitch`, `cemetery`, `industrial`, `commercial`, `ice`,
`runway`, `minor_casing`. Missing ones are derived from the skin's palette.

## Themed skins

`skins/` holds forty finished themes to learn from and to copy. Pick one in the
dropdown at the top-left, then open its file and edit it live:

| file                   | look                                                        | tricks it uses |
|------------------------|-------------------------------------------------------------|----------------|
| `skins/frontier.json`  | sepia parchment, cream roads with dark edges, uppercase condensed labels | road casing (two line layers), `text-transform`, `text-letter-spacing`, paper vignette overlay |
| `skins/empire.json`    | dark asphalt, light-grey roads, bold white labels           | dark palette, strong `text-halo` |
| `skins/cybershock.json`| crimson blocks, glowing cyan roads, yellow rails            | glow = wide blurred line under a thin bright one (`line-blur`, `line-opacity`), scanline overlay |
| `skins/cubeworld.json` | 3D grey blocks on green ground, tilted camera               | `fill-extrusion` buildings using `render_height`, pitch/bearing preset |
| `skins/wasteland.json` | green-on-black terminal                                     | outlined buildings (`fill-outline-color`), glow roads, scanlines |
| `skins/sanandreas.json`| white paper, thick black streets, brown highways            | an extra `road-highway` layer on top of major roads |
| `skins/zellige.json`   | Fès mosaic: cream, cobalt water, emerald gardens, terracotta houses, white lanes edged in blue | coloured casings, diamond-lattice overlay |
| `skins/sahara.json`    | dunes: warm sand, turquoise oases, adobe houses, red highways | separate `sand`/`rock` colours, warm vignette |
| `skins/medina.json`    | Marrakech red city: ochre-pink ground, deep red houses, cream lanes | paper vignette |
| `skins/chefchaouen.json`| the blue town: washed blue ground, blue houses, white lanes, indigo water | light palette with dark text halo |
| `skins/atlas.json`     | High Atlas: pale valleys, cedar green, grey-brown rock, peaks with heights | strong `rock` colour, peak labels matter here |
| `skins/amazigh.json`   | flag colours: yellow ground, green land, blue water and lanes, red houses | uppercase labels |
| `skins/ramadan.json`   | indigo night, gold-lit boulevards                            | glow roads, starry overlay |
| `skins/essaouira.json` | whitewashed houses outlined in blue on an Atlantic blue      | building outline carries the look, no minor casing |
| `skins/tafraout.json`  | pink granite, argan green, painted blue rocks as houses      | warm vignette |
| `skins/relief.json`    | the Atlas skin plus forests as blocks                        | `extrude_forest` |
| `skins/minttea.json`   | mint green ground, gold houses, green-edged lanes            | |
| `skins/argan.json`     | the Souss: olive groves, honey houses, straw ground          | warm vignette |
| `skins/ifrane.json`    | snow: white ground, cedar blocks, wooden chalets, blue shadows | `extrude_forest`, custom `shade` colour |
| `skins/dakhla.json`    | the lagoon: turquoise water, pale sand, white houses, orange highways | |
| `skins/caftan.json`    | royal purple with gold-glowing roads and magenta houses      | glow roads |
| `skins/blueprint.json` | engineering drawing: blue paper, white ink, uppercase        | no casings, `text-transform` |
| `skins/sketch.json`    | pencil on cream paper                                        | paper overlay, PT Sans Caption |
| `skins/noir.json`      | pure black and white, high contrast                          | heavy `text-halo` |

**City skins** (`skins/casablanca.json`, `rabat`, `fes`, `tanger`, `agadir`,
`meknes`, `tetouan`, `oujda`, `ouarzazate`, `eljadida`, `laayoune`, `kenitra`,
`safi`, `nador`, `benimellal`): one palette per city, drawn from the city's
own character (Art Deco white and Atlantic blue for Casablanca, Oudayas
blue-and-white for Rabat, Fès green and ochre, Bab Mansour green and gold for
Meknès, kasbah red earth for Ouarzazate, pottery blue for Safi…). Each
carries its home coordinates in `metadata.playground.center` / `zoom`, so
picking it in the dropdown flies to that city. The place skins (medina,
chefchaouen, essaouira, tafraout, ifrane, dakhla, sahara, atlas, relief) fly
home the same way.

**Country skins** (`skins/country/<code>.json`, 250 of them): one per
country, generated, not hand-made. The colours come from the country's flag:
the dominant colour becomes a pale ground tint, the second colour the houses,
the third the highways, the darkest the road outlines and text; blue and green
in the flag tint the water and parks. Picking one flies to the capital (193
capitals located from Natural Earth; the rest land on the country centre).
They are generated by `tools/make_skins.py` from `tools/countries_palette.json`,
which `tools/country_palettes.py` builds from the flag images (see `tools/README.md`). Edit the mapping in
`country()` to change all 250 at once, or copy one file out of `country/`
and hand-tune it like any other skin.

The dropdown is grouped: Moroccan cities, Themes, Countries, Mine. Type in the
"Find a skin" box (or press `/`) to filter it; Enter picks the first match.
| `skins/earth.json`     | **Globe**: satellite imagery of the whole planet, with roads, borders and names drawn over it | `raster` source (Esri imagery), `"projection": {"type": "globe"}`, no vector ground layers |

All of them share the same layer skeleton, in the same order. Open two side by
side and diff them: only colours, widths, fonts and a few extra layers change.
That skeleton is a good template for your own `style.json`.

Things only the playground understands live under `metadata.playground`:

    "metadata": { "playground": { "overlay": "scanlines", "pitch": 55, "bearing": -17 } }

`overlay` is `scanlines`, `paper`, `zellige`, `heat` or `stars` (CSS in `index.html`, add your own).
`pitch`/`bearing` are applied once when you select the skin.

## 3D

**Every skin is 3D**: real terrain, shaded slopes, houses at their true
height, and a tilted camera when you select it. Three things make that
happen, and each is a few lines you can tune or remove per skin:

1. **Terrain**: a `raster-dem` source (free Terrarium elevation tiles from AWS)
   plus a root `"terrain": {"source": "dem", "exaggeration": 1.3}`. The whole
   map drapes over the real relief: mountains rise, rivers sit in valleys.
   Add a `"sky"` block for a horizon when tilted.
2. **Hillshade**: a `hillshade` layer on the same `dem` source, placed after
   the ground colours, gives shading on slopes even when looking straight down.
3. **Extrusion**: `fill-extrusion` layers. Houses use the tiles'
   `render_height`; forests use a fixed 14 m. Anything with a polygon can be
   extruded: try parks at 1 m, or water at -2 m for sunken rivers.

Tilt with right-drag (or Ctrl+drag), rotate with the compass. To make a skin
flat again, delete its `terrain` and `sky` blocks and its `hillshade` layer,
and change the `building` layer's type from `fill-extrusion` to `fill`.

## Globe

The **Globe** button draws any skin on a sphere; zoom out (or pick "Whole
Earth" in the city list) to see the planet. A skin can ask for it itself with

    "projection": { "type": "globe" }

at the top level, which is what `skins/earth.json` does. That skin is
different from the others: the ground is a `raster` layer of satellite
imagery instead of coloured polygons, and only roads, borders and names come
from the vector tiles. Replace the imagery URL with any other XYZ tile
service to change the ground.

Add your own skin: copy a file into `skins/`, add a line to `skins.json`.

## Fonts and scripts

Every label asks for the skin's font first and **Noto Sans** second
(`"text-font": ["Metropolis Bold", "Noto Sans Bold"]`). The server merges
the two glyph files, so Arabic, Chinese or any script the skin font lacks
still renders, in Noto. Arabic is shaped right-to-left by the RTL plugin the
viewer loads.

## Available fonts

Skins use fonts served from the parent project's `fonts/` folder at
`/fonts/{fontstack}/{range}.pbf`. Available stacks (use the names exactly):

- **Noto Sans** Regular, Bold, Italic (also the only ones OpenFreeMap serves online)
- **Roboto** Thin, Light, Regular, Medium, Bold, Black + italics
- **Roboto Condensed** Light, Regular, Bold + italics
- **Metropolis** Thin … Black (nine weights) + italics
- **Open Sans** Light, Regular, Semibold, Bold, Extra Bold + italics
- **PT Sans** Regular, Bold, Narrow Regular, Narrow Bold, Caption + italics

Pixel or "game" typefaces are not in the set. To add one, convert a `.ttf`
with https://maplibre.org/font-maker/ and drop the folder into `fonts/`.

## Using a skin in another app (naviq, Missions, …)

The playground server already serves every skin as a ready-to-use MapLibre
style URL, with open CORS and absolute font URLs:

    http://localhost:3030/skins/frontier.json
    http://localhost:3030/skins/empire.json
    http://localhost:3030/skins/cybershock.json
    http://localhost:3030/skins/cubeworld.json
    http://localhost:3030/skins/wasteland.json
    http://localhost:3030/skins/sanandreas.json
    http://localhost:3030/style.json              (your own)

Web (MapLibre GL JS):

    new maplibregl.Map({ container: 'map', style: 'http://localhost:3030/skins/frontier.json' })

Flutter (maplibre_gl):

    MapLibreMap(styleString: 'http://192.168.x.x:3000/skins/frontier.json', ...)

A phone cannot reach `localhost` on your PC: use the PC's LAN IP instead.
The server fills in the font URLs from whatever host you used, so the same
file works from both. Keep `python serve.py` running while the app runs.
Edits to a skin file show up in the app on its next style load.

The tiles themselves come from OpenFreeMap (free, no key, fair use). For
offline or production use, switch the source `url` to your own tile server:
the Docker setup in the parent folder serves `mbtiles://{morocco}`.

## When something breaks

- Red pill top-left: your JSON does not parse, or MapLibre rejected a
  property. The message says which.
- Layer added but nothing appears: check `source-layer` spelling, the
  `filter` values (click a feature to see real tags), and `minzoom`.
- Label missing: check the font name exactly, and that the feature has
  the tag you asked for (`name:fr` is absent on many small places, hence
  `coalesce`).
- The map keeps its camera on reload. Reload the page itself if the whole
  thing looks stuck.

## Taking it further

- Paste `style.json` into https://maputnik.github.io/editor for a visual
  editor; copy the result back.
- Specification of every property:
  https://maplibre.org/maplibre-style-spec/
- When you are happy, the same `style.json` works in the Docker tile server
  in the parent folder: copy it to `styles/missions/style.json` and change
  the source `url` back to `mbtiles://{morocco}`.
