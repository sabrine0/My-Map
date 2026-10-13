import json, os, re
OUT = r"C:\Users\sabri\Desktop\My Map\playground\skins"
os.makedirs(OUT, exist_ok=True)
GLYPHS = "/fonts/{fontstack}/{range}.pbf"
SPRITE = "https://tiles.openfreemap.org/sprites/ofm_f384/ofm"
SRC = {"osm": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}}
# Free elevation tiles (Mapzen/Tilezen Terrarium on AWS Open Data). Used for 3D terrain + hillshade.
DEM = {"type": "raster-dem", "encoding": "terrarium", "tileSize": 256, "maxzoom": 15,
       "tiles": ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
       "attribution": "Terrain: Mapzen / AWS Open Data"}

def z(*stops):  # z(6,1, 10,2) -> interpolate on zoom
    return ["interpolate", ["linear"], ["zoom"], *stops]
MINOR = ["in", "class", "minor", "service", "tertiary"]
MAJOR = ["in", "class", "motorway", "trunk", "primary", "secondary"]
HIGHWAY = ["in", "class", "motorway", "trunk"]
W_MINOR = z(11, 0.4, 14, 1.8, 17, 6)
W_MAJOR = z(5, 1.0, 8, 1.4, 10, 1.9, 14, 4, 17, 10)     # visible from country zoom
W_HWY   = z(4, 1.3, 8, 2.0, 10, 2.8, 14, 6, 17, 14)
def _map_outputs(width, fn):
    # width is ["interpolate", ["linear"], ["zoom"], z1, w1, z2, w2, ...]
    head, stops = width[:3], width[3:]
    out = list(head)
    for i in range(0, len(stops), 2):
        out += [stops[i], round(fn(stops[i + 1]), 2)]
    return out
def plus(width, n):   # same stops, each output + n  (for casings)
    return _map_outputs(width, lambda w: w + n)
def times(width, n):  # same stops, each output * n  (for glows)
    return _map_outputs(width, lambda w: w * n)


# POI classes that have an icon in the OpenFreeMap sprite (names without the "_11" size suffix)
_SPRITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite.json")
_skip = re.compile(r"^(road_|us-|default_|dot_|circle|square|triangle|star|marker|arrow|oneway|pedestrian_polygon|wetland_bg|building|heart|cross|danger)")
POI_CLASSES = sorted({k[:-3] if k.endswith("_11") else k for k in json.load(open(_SPRITE))} - {""})
POI_CLASSES = [c for c in POI_CLASSES if not _skip.match(c)]

def _lum(c):
    r, g, b = _hex(c); return (0.299 * r + 0.587 * g + 0.114 * b) / 255

NOT_TUNNEL = ["!=", "brunnel", "tunnel"]
SORT = {"line-sort-key": ["coalesce", ["get", "layer"], 0]}   # overpasses above underpasses

def build(t):
    L = []
    add = L.append
    bg = t["bg"]; dark = _lum(bg) < 0.4
    green = t["green"]
    # derived tints: every one can be overridden per skin with the same key
    wood = t.get("wood", _mix(green, "#000000", 0.18))
    grass = t.get("grass", _mix(green, "#ffffff", 0.22) if not dark else _mix(green, "#ffffff", 0.08))
    wet = t.get("wetland", _mix(green, t["water"], 0.45))
    civic = t.get("civic", _mix(bg, t["building"], 0.16))
    pitch = t.get("pitch", _mix(green, "#000000" if dark else "#ffffff", 0.12))
    cemetery = t.get("cemetery", _mix(green, bg, 0.45))
    industrial = t.get("industrial", _mix(t["landuse"], t.get("rock", bg), 0.5))
    commercial = t.get("commercial", _mix(t["landuse"], t["building"], 0.08))
    ice = t.get("ice", _mix(bg, "#ffffff", 0.25) if dark else "#f4f8fb")
    runway = t.get("runway", _mix(t["minor"], "#000000", 0.25))
    minor_casing = t.get("minor_casing", _mix(t["minor"], "#000000", 0.55 if dark else 0.4))
    bc = t["building"]
    lighter = _mix(bc, "#ffffff", 0.35) if _lum(bc) < 0.75 else _mix(bc, "#000000", 0.18)
    disc = "#ffffff"                                    # under POI icons (icons are dark bitmaps)
    disc_stroke = t["text"] if not dark else _mix(t["text"], "#000000", 0.5)

    add({"id": "background", "type": "background", "paint": {"background-color": bg}})
    # ---- ground ---------------------------------------------------------
    add({"id": "landuse-residential", "type": "fill", "source": "osm", "source-layer": "landuse",
         "filter": ["in", "class", "residential", "suburb", "neighbourhood", "quarter"],
         "paint": {"fill-color": t["landuse"]}})
    add({"id": "landuse-commercial", "type": "fill", "source": "osm", "source-layer": "landuse",
         "minzoom": 10, "filter": ["in", "class", "commercial", "retail"],
         "paint": {"fill-color": commercial}})
    add({"id": "landuse-industrial", "type": "fill", "source": "osm", "source-layer": "landuse",
         "minzoom": 9, "filter": ["in", "class", "industrial", "quarry", "railway", "garages", "military"],
         "paint": {"fill-color": industrial, "fill-opacity": 0.8}})
    add({"id": "landcover-farmland", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "farmland"],
         "paint": {"fill-color": t.get("farmland", t["landuse"]), "fill-opacity": 0.8}})
    add({"id": "landcover-sand", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "sand"], "paint": {"fill-color": t.get("sand", bg)}})
    add({"id": "landcover-rock", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "rock"], "paint": {"fill-color": t.get("rock", t["landuse"]), "fill-opacity": 0.8}})
    add({"id": "landcover-ice", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "ice"], "paint": {"fill-color": ice, "fill-opacity": 0.9}})
    add({"id": "landcover-grass", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "grass"], "paint": {"fill-color": grass, "fill-opacity": 0.7}})
    add({"id": "landcover-wood", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "wood"], "paint": {"fill-color": wood, "fill-opacity": 0.75}})
    add({"id": "landcover-wetland", "type": "fill", "source": "osm", "source-layer": "landcover",
         "filter": ["==", "class", "wetland"], "paint": {"fill-color": wet, "fill-opacity": 0.6}})
    add({"id": "landuse-civic", "type": "fill", "source": "osm", "source-layer": "landuse",
         "minzoom": 11, "filter": ["in", "class", "hospital", "school", "college", "university", "kindergarten"],
         "paint": {"fill-color": civic}})
    add({"id": "landuse-cemetery", "type": "fill", "source": "osm", "source-layer": "landuse",
         "minzoom": 11, "filter": ["in", "class", "cemetery", "grave_yard"],
         "paint": {"fill-color": cemetery}})
    add({"id": "landuse-pitch", "type": "fill", "source": "osm", "source-layer": "landuse",
         "minzoom": 12, "filter": ["in", "class", "pitch", "playground", "stadium", "track", "sports_centre",
                                   "golf_course", "garden", "zoo", "theme_park"],
         "paint": {"fill-color": pitch, "fill-outline-color": _mix(pitch, "#000000", 0.3)}})
    # national parks and reserves exist from zoom 5; city parks from 13
    add({"id": "park", "type": "fill", "source": "osm", "source-layer": "park",
         "paint": {"fill-color": green, "fill-opacity": z(5, 0.35, 10, 0.5, 13, 0.85)}})
    add({"id": "park-outline", "type": "line", "source": "osm", "source-layer": "park", "minzoom": 14,
         "paint": {"line-color": _mix(green, "#000000", 0.3), "line-width": 0.6, "line-opacity": 0.6}})
    if t.get("terrain"):
        add({"id": "hillshade", "type": "hillshade", "source": "dem",
             "paint": {"hillshade-exaggeration": t.get("hillshade", 0.45),
                       "hillshade-shadow-color": t.get("shade", "#3a2e1e"),
                       "hillshade-highlight-color": t.get("highlight", "#ffffff"),
                       "hillshade-accent-color": t.get("shade", "#3a2e1e")}})
    # airports: apron/aerodrome areas, then runways and taxiways as thick lines
    add({"id": "aeroway-area", "type": "fill", "source": "osm", "source-layer": "aeroway", "minzoom": 10,
         "filter": ["all", ["==", "$type", "Polygon"], ["in", "class", "aerodrome", "apron", "heliport"]],
         "paint": {"fill-color": industrial, "fill-opacity": 0.6}})
    add({"id": "aeroway-taxiway", "type": "line", "source": "osm", "source-layer": "aeroway", "minzoom": 11,
         "filter": ["==", "class", "taxiway"],
         "paint": {"line-color": runway, "line-width": z(11, 0.5, 14, 2, 16, 5)}})
    add({"id": "aeroway-runway", "type": "line", "source": "osm", "source-layer": "aeroway", "minzoom": 10,
         "filter": ["==", "class", "runway"],
         "paint": {"line-color": runway, "line-width": z(10, 0.8, 14, 5, 16, 16)}})
    if t.get("extrude_forest"):
        add({"id": "forest-3d", "type": "fill-extrusion", "source": "osm", "source-layer": "landcover",
             "minzoom": 12, "filter": ["==", "class", "wood"],
             "paint": {"fill-extrusion-color": wood, "fill-extrusion-height": 14,
                       "fill-extrusion-opacity": 0.9, "fill-extrusion-vertical-gradient": True}})
    # ---- water ----------------------------------------------------------
    water_paint = {"fill-color": t["water"]}
    if t.get("water_outline"):
        water_paint["fill-outline-color"] = t["water_line"]
    add({"id": "water", "type": "fill", "source": "osm", "source-layer": "water",
         "filter": ["!=", "intermittent", 1], "paint": water_paint})
    add({"id": "water-shore", "type": "line", "source": "osm", "source-layer": "water", "minzoom": 11,
         "filter": ["!=", "intermittent", 1],
         "paint": {"line-color": t["water_line"], "line-width": 0.8, "line-opacity": 0.5}})
    river = lambda a, b: ["match", ["get", "class"], "river", a, "canal", round(a * 0.8, 2), b]
    add({"id": "waterway", "type": "line", "source": "osm", "source-layer": "waterway",
         "filter": ["in", "class", "river", "canal"], "layout": {"line-cap": "round"},
         "paint": {"line-color": t["water_line"],
                   "line-width": z(4, 0.4, 10, river(1.0, 0.6), 14, river(2.2, 1.2), 17, river(6, 3))}})
    add({"id": "waterway-small", "type": "line", "source": "osm", "source-layer": "waterway", "minzoom": 13,
         "filter": ["in", "class", "stream", "ditch", "drain"],
         "paint": {"line-color": t["water_line"], "line-width": z(13, 0.5, 17, 2), "line-opacity": 0.8}})
    # ---- buildings: taller is lighter (or darker on pale skins), lit from the top-left
    if t.get("extrude"):
        add({"id": "building", "type": "fill-extrusion", "source": "osm", "source-layer": "building",
             "minzoom": 13,
             "paint": {"fill-extrusion-color": ["interpolate", ["linear"], ["coalesce", ["get", "render_height"], 8],
                                                0, bc, 20, _mix(bc, lighter, 0.4), 60, lighter],
                       "fill-extrusion-height": ["coalesce", ["get", "render_height"], 8],
                       "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
                       "fill-extrusion-opacity": z(13, 0.6, 15, 0.95),
                       "fill-extrusion-vertical-gradient": True}})
    else:
        add({"id": "building", "type": "fill", "source": "osm", "source-layer": "building", "minzoom": 12,
             "paint": {"fill-color": bc, "fill-outline-color": t["building_line"], "fill-opacity": z(12, 0.4, 14, 1)}})
    # ---- roads ----------------------------------------------------------
    round_ = {"line-cap": "round", "line-join": "round", **SORT}
    butt = {"line-cap": "butt", "line-join": "round", **SORT}
    ROADS = ["in", "class", "minor", "tertiary", "service", "motorway", "trunk", "primary", "secondary"]
    # tunnels: dashed outline, faded fill, under everything else
    add({"id": "road-tunnel-casing", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 12, "filter": ["all", ROADS, ["==", "brunnel", "tunnel"]], "layout": butt,
         "paint": {"line-color": minor_casing, "line-width": plus(W_MAJOR, 2), "line-dasharray": [3, 2],
                   "line-opacity": 0.6}})
    add({"id": "road-tunnel", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 12, "filter": ["all", ROADS, ["==", "brunnel", "tunnel"]], "layout": butt,
         "paint": {"line-color": t["minor"], "line-width": W_MAJOR, "line-opacity": 0.5}})
    add({"id": "road-path", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 14, "filter": ["in", "class", "path", "track", "pedestrian"],
         "paint": {"line-color": t.get("path", t["minor"]), "line-width": z(14, 0.6, 17, 2),
                   "line-dasharray": [2, 2], "line-opacity": 0.8}})
    W_SERVICE = z(13, 0.3, 15, 1, 17, 3.5)
    add({"id": "road-service-casing", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 14, "filter": ["all", ["==", "class", "service"], NOT_TUNNEL], "layout": round_,
         "paint": {"line-color": minor_casing, "line-width": plus(W_SERVICE, 1.2), "line-opacity": 0.8}})
    add({"id": "road-service", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 13, "filter": ["all", ["==", "class", "service"], NOT_TUNNEL], "layout": round_,
         "paint": {"line-color": t["minor"], "line-width": W_SERVICE}})
    MINOR2 = ["in", "class", "minor", "tertiary"]
    add({"id": "road-minor-casing", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 12, "filter": ["all", MINOR2, NOT_TUNNEL], "layout": round_,
         "paint": {"line-color": minor_casing, "line-width": plus(W_MINOR, 1.5)}})
    add({"id": "road-minor", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 11, "filter": ["all", MINOR2, NOT_TUNNEL], "layout": round_,
         "paint": {"line-color": t["minor"], "line-width": W_MINOR}})
    if t.get("glow"):
        add({"id": "road-major-glow", "type": "line", "source": "osm", "source-layer": "transportation",
             "filter": ["all", MAJOR, NOT_TUNNEL], "layout": round_,
             "paint": {"line-color": t["glow"], "line-width": times(W_MAJOR, 3.5), "line-blur": 3, "line-opacity": 0.45}})
    if t.get("major_casing"):
        add({"id": "road-major-casing", "type": "line", "source": "osm", "source-layer": "transportation",
             "filter": ["all", MAJOR, NOT_TUNNEL], "layout": round_,
             "paint": {"line-color": t["major_casing"], "line-width": plus(W_MAJOR, 2)}})
    add({"id": "road-major", "type": "line", "source": "osm", "source-layer": "transportation",
         "filter": ["all", MAJOR, NOT_TUNNEL], "layout": round_,
         "paint": {"line-color": t["major"], "line-width": W_MAJOR}})
    if t.get("highway"):
        add({"id": "road-highway", "type": "line", "source": "osm", "source-layer": "transportation",
             "filter": ["all", HIGHWAY, NOT_TUNNEL], "layout": round_,
             "paint": {"line-color": t["highway"], "line-width": W_HWY}})
    if not dark:   # the arrow glyph is dark; only readable on light roads
        add({"id": "road-oneway", "type": "symbol", "source": "osm", "source-layer": "transportation",
             "minzoom": 16, "filter": ["all", ["in", "class", "minor", "tertiary", "secondary", "primary"],
                                       ["in", "oneway", 1, -1]],
             "layout": {"symbol-placement": "line", "symbol-spacing": 140, "icon-image": "arrow",
                        "icon-size": 0.55, "icon-rotate": ["match", ["get", "oneway"], -1, 180, 0],
                        "icon-rotation-alignment": "map", "icon-padding": 2, "icon-ignore-placement": True},
             "paint": {"icon-opacity": 0.45}})
    # rails: a line plus "sleepers" (short wide dashes)
    add({"id": "rail", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 11, "filter": ["all", ["==", "class", "rail"], NOT_TUNNEL], "layout": SORT,
         "paint": {"line-color": t["rail"], "line-width": z(11, 0.6, 16, 2.2), "line-opacity": 0.8}})
    add({"id": "rail-ties", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 13, "filter": ["all", ["==", "class", "rail"], NOT_TUNNEL], "layout": SORT,
         "paint": {"line-color": t["rail"], "line-width": z(13, 2.5, 16, 6), "line-dasharray": [0.2, 2.5],
                   "line-opacity": 0.6}})
    add({"id": "transit", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 13, "filter": ["in", "class", "transit", "tram", "light_rail", "subway"],
         "paint": {"line-color": t["rail"], "line-width": z(13, 0.8, 16, 2), "line-dasharray": [2, 2], "line-opacity": 0.7}})
    # ---- boundaries -----------------------------------------------------
    add({"id": "boundary-region", "type": "line", "source": "osm", "source-layer": "boundary",
         "maxzoom": 13, "filter": ["all", ["==", "admin_level", 4], ["!=", "maritime", 1]],
         "paint": {"line-color": t["boundary"], "line-width": z(4, 0.4, 10, 1), "line-opacity": 0.5, "line-dasharray": [2, 3]}})
    add({"id": "boundary-country", "type": "line", "source": "osm", "source-layer": "boundary",
         "filter": ["all", ["==", "admin_level", 2], ["!=", "disputed", 1], ["!=", "maritime", 1]],
         "paint": {"line-color": t["boundary"], "line-width": z(3, 0.8, 10, 2), "line-dasharray": [4, 2]}})
    # ---- labels ---------------------------------------------------------
    name = ["coalesce", ["get", "name:fr"], ["get", "name"]]
    font, bold, italic = t["font"], t.get("font_bold", t["font"]), t.get("font_italic", t["font"])
    base_layout = {"text-font": font, "text-transform": t.get("transform", "none"),
                   "text-letter-spacing": t.get("spacing", 0)}
    text_paint = {"text-color": t["text"], "text-halo-color": t["text_halo"], "text-halo-width": t.get("halo_w", 1.4)}
    add({"id": "housenumber", "type": "symbol", "source": "osm", "source-layer": "housenumber", "minzoom": 17,
         "layout": {"text-font": font, "text-field": ["get", "housenumber"], "text-size": 9, "text-padding": 4},
         "paint": {**text_paint, "text-opacity": 0.7, "text-halo-width": 1}})
    add({"id": "road-label", "type": "symbol", "source": "osm", "source-layer": "transportation_name",
         "minzoom": 13, "filter": ["all", ["!=", "class", "rail"], NOT_TUNNEL],
         "layout": {**base_layout, "symbol-placement": "line", "text-field": name,
                    "text-size": z(13, 10, 17, 13), "text-max-angle": 30, "symbol-spacing": 300},
         "paint": text_paint})
    # highway number shields (the sprite has boxes sized for 1 to 6 characters)
    add({"id": "road-shield", "type": "symbol", "source": "osm", "source-layer": "transportation_name",
         "minzoom": 7, "filter": ["all", ["has", "ref"], ["<=", "ref_length", 6],
                                  ["in", "class", "motorway", "trunk", "primary"]],
         "layout": {"symbol-placement": "line", "symbol-spacing": 400,
                    "icon-image": ["match", ["get", "network"], ["us-highway", "us-interstate", "us-state"],
                                   ["concat", ["get", "network"], "_", ["to-string", ["get", "ref_length"]]],
                                   ["concat", "road_", ["to-string", ["get", "ref_length"]]]],
                    "icon-rotation-alignment": "viewport", "icon-pitch-alignment": "viewport",
                    "text-field": ["get", "ref"], "text-font": bold, "text-size": 9,
                    "text-rotation-alignment": "viewport", "text-pitch-alignment": "viewport"},
         "paint": {"text-color": "#222222"}})
    add({"id": "waterway-label", "type": "symbol", "source": "osm", "source-layer": "waterway", "minzoom": 12,
         "filter": ["all", ["has", "name"], ["in", "class", "river", "canal"]],
         "layout": {**base_layout, "symbol-placement": "line", "text-field": name, "text-size": 11,
                    "text-font": italic, "symbol-spacing": 400},
         "paint": {**text_paint, "text-color": t.get("water_text", t["text"])}})
    add({"id": "water-label", "type": "symbol", "source": "osm", "source-layer": "water_name",
         "layout": {**base_layout, "text-field": name, "text-size": 12, "symbol-placement": "line", "text-font": italic},
         "paint": {**text_paint, "text-color": t.get("water_text", t["text"])}})
    # POIs: a white disc, the icon, the name. Important ones from z14, the rest from z16.
    icon = ["match", ["get", "subclass"], ["florist", "furniture"], ["get", "subclass"], ["get", "class"]]
    for tier, (mz, flt) in {"a": (15, ["<=", "rank", 10]), "b": (16.5, [">", "rank", 10])}.items():
        # only POI classes the sprite has an icon for, so no empty discs
        f = ["all", ["has", "name"], flt, ["==", "$type", "Point"], ["in", "class", *POI_CLASSES]]
        add({"id": f"poi-disc-{tier}", "type": "circle", "source": "osm", "source-layer": "poi", "minzoom": mz, "filter": f,
             "paint": {"circle-radius": z(14, 7, 17, 9), "circle-color": disc, "circle-opacity": 0.92,
                       "circle-stroke-color": disc_stroke, "circle-stroke-width": 1, "circle-pitch-alignment": "viewport"}})
        add({"id": f"poi-{tier}", "type": "symbol", "source": "osm", "source-layer": "poi", "minzoom": mz, "filter": f,
             # the disc below is a circle layer that always draws, so the icon must
             # always draw too (never collision-hidden); only the name competes for space
             "layout": {**base_layout, "icon-image": icon, "icon-size": z(14, 0.55, 17, 0.75),
                        "icon-allow-overlap": True, "icon-ignore-placement": True,
                        "symbol-sort-key": ["coalesce", ["get", "rank"], 30],
                        "text-field": name, "text-size": 10, "text-max-width": 8,
                        "text-anchor": "top", "text-offset": [0, 0.9], "text-optional": True, "icon-padding": 1},
             "paint": {**text_paint, "text-opacity": 0.9}})
    add({"id": "peak-label", "type": "symbol", "source": "osm", "source-layer": "mountain_peak",
         "minzoom": 9, "filter": ["all", ["has", "name"], ["==", "class", "peak"]],
         "layout": {**base_layout, "text-font": italic,
                    "text-field": ["concat", name, "\n", ["to-string", ["get", "ele"]], " m"],
                    "text-size": 10, "text-max-width": 7},
         "paint": {**text_paint, "text-opacity": 0.8}})
    add({"id": "place-village", "type": "symbol", "source": "osm", "source-layer": "place",
         "minzoom": 9, "filter": ["in", "class", "village", "hamlet", "suburb", "neighbourhood", "quarter"],
         "layout": {**base_layout, "text-field": name, "text-size": z(9, 9, 14, 12)},
         "paint": {**text_paint, "text-opacity": 0.85}})
    # towns and cities get a dot when zoomed out, text centred when zoomed in
    dot_off = lambda zz: ["step", ["zoom"], ["literal", [0, 0.6]], zz, ["literal", [0, 0]]]
    dot_anchor = lambda zz: ["step", ["zoom"], "top", zz, "center"]
    add({"id": "place-town-dot", "type": "circle", "source": "osm", "source-layer": "place",
         "minzoom": 6, "maxzoom": 10, "filter": ["==", "class", "town"],
         "paint": {"circle-radius": 2.5, "circle-color": t["text"], "circle-stroke-color": t["text_halo"],
                   "circle-stroke-width": 1, "circle-pitch-alignment": "viewport"}})
    add({"id": "place-town", "type": "symbol", "source": "osm", "source-layer": "place",
         "minzoom": 6, "filter": ["==", "class", "town"],
         "layout": {**base_layout, "text-field": name, "text-size": z(6, 9, 10, 11, 14, 14),
                    "text-offset": dot_off(10), "text-anchor": dot_anchor(10)},
         "paint": text_paint})
    add({"id": "place-state", "type": "symbol", "source": "osm", "source-layer": "place",
         "minzoom": 5, "maxzoom": 10, "filter": ["in", "class", "state", "province"],
         "layout": {**base_layout, "text-field": name, "text-size": z(5, 9, 9, 13),
                    "text-transform": "uppercase", "text-letter-spacing": 0.2, "text-max-width": 7},
         "paint": {**text_paint, "text-opacity": 0.6}})
    cap = ["==", ["get", "capital"], 2]
    add({"id": "place-city-dot", "type": "circle", "source": "osm", "source-layer": "place",
         "maxzoom": 9, "filter": ["==", "class", "city"],
         "paint": {"circle-radius": ["case", cap, 4.5, 3], "circle-color": t["text"],
                   "circle-stroke-color": t["text_halo"], "circle-stroke-width": 1.5, "circle-pitch-alignment": "viewport"}})
    add({"id": "place-city", "type": "symbol", "source": "osm", "source-layer": "place",
         "filter": ["==", "class", "city"],
         "layout": {**base_layout, "text-field": name, "text-font": bold,
                    "text-size": z(4, ["case", cap, 13, 11], 8, ["case", cap, 17, 14], 12, ["case", cap, 24, 20]),
                    "text-offset": dot_off(9), "text-anchor": dot_anchor(9)},
         "paint": text_paint})
    add({"id": "place-country", "type": "symbol", "source": "osm", "source-layer": "place",
         "maxzoom": 7, "filter": ["==", "class", "country"],
         "layout": {**base_layout, "text-field": name, "text-size": z(2, 11, 6, 18), "text-font": bold,
                    "text-transform": "uppercase", "text-letter-spacing": 0.15},
         "paint": text_paint})
    style = {"version": 8, "name": t["name"], "metadata": {"playground": t.get("meta", {})},
             "sources": dict(SRC), "glyphs": GLYPHS, "sprite": SPRITE,
             "light": {"anchor": "viewport", "color": "#ffffff", "intensity": 0.3 if dark else 0.4, "position": [1.15, 210, 30]},
             "layers": L}
    if t.get("terrain"):
        style["sources"]["dem"] = DEM
        style["terrain"] = {"source": "dem", "exaggeration": t.get("exaggeration", 1.3)}
        style["sky"] = {"sky-color": t.get("sky", "#8fbce6"), "horizon-color": t.get("horizon", "#e9ddc8"),
                        "fog-color": t.get("fog", bg), "sky-horizon-blend": 0.6,
                        # fog only near the horizon, so it never tints water and roads mid-screen
                        "horizon-fog-blend": 0.8, "fog-ground-blend": 0.9, "atmosphere-blend": 0.8}
    return style

THEMES = {
 "frontier": dict(name="Old Wild Frontier",
    bg="#c7b38a", landuse="#bfa97e", green="#aeae7c", water="#9db3a2", water_line="#7f9a88",
    farmland="#c2b088", sand="#d4c198", rock="#b5a27c",
    building="#a68f6e", building_line="#7a664a",
    minor="#e6d9bb", minor_casing="#6e5b3f", major="#f1e5c8", major_casing="#4f3f29", highway="#d8bf90",
    rail="#5a4830", boundary="#4f3f29",
    font=["Roboto Condensed Bold"], font_bold=["Roboto Condensed Bold"], font_italic=["Roboto Condensed Italic"],
    transform="uppercase", spacing=0.08, text="#2e2416", text_halo="#e9dcbc", halo_w=1.2,
    meta={"overlay": "paper"}),
 "empire": dict(name="Great Street Empire",
    bg="#262626", landuse="#2b2b2b", green="#2d3a2d", water="#161e26", water_line="#1f2d3a",
    farmland="#292c27", sand="#2d2b26", rock="#2f2f2f",
    building="#383838", building_line="#464646",
    minor="#8a8a8a", major="#dcdcdc", major_casing="#111111", highway="#f4f4f4",
    rail="#5a5a5a", boundary="#9a9a9a",
    font=["Metropolis Extra Bold"], font_bold=["Metropolis Black"], font_italic=["Metropolis Bold Italic"],
    transform="none", spacing=0.02, text="#f3f3f3", text_halo="#0d0d0d", halo_w=1.6, meta={}),
 "cybershock": dict(name="Cybershock 2099",
    bg="#6c1a35", landuse="#75203c", green="#1d4747", water="#10263a", water_line="#1f6f8a",
    farmland="#651a33", sand="#7a2742", rock="#5a1630",
    building="#8b2a4b", building_line="#3f0c21", extrude=True,
    minor="#1e8fb3", glow="#19c3f0", major="#5fe6ff", highway="#c9fbff",
    rail="#ffd400", boundary="#ffd400",
    font=["Open Sans Semibold"], font_bold=["Open Sans Extra Bold"], font_italic=["Open Sans Italic"],
    transform="none", spacing=0, text="#86f0ff", text_halo="#2a0613", halo_w=1.3,
    meta={"overlay": "scanlines", "pitch": 50, "bearing": -20}),
 "cubeworld": dict(name="Cubeworld",
    bg="#6b8f52", landuse="#79866a", green="#4f9a3a", water="#3b67d4", water_line="#2f55b8",
    farmland="#86a35c", sand="#d9c98a", rock="#8c8c82",
    building="#6b7280", building_line="#4b5160", extrude=True,
    minor="#c6b073", minor_casing="#5a4a2a", major="#dbc47c", major_casing="#4a3c20",
    rail="#8a7a5a", boundary="#f0e68c",
    font=["PT Sans Bold"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"],
    transform="none", spacing=0.02, text="#dcf5b8", text_halo="#1f3a1a", halo_w=1.5,
    meta={"pitch": 55, "bearing": -17}),
 "wasteland": dict(name="Wasteland 4",
    bg="#06220a", landuse="#082a0d", green="#0b3611", water="#062a17", water_line="#2cff5a", water_outline=True,
    farmland="#07270c", sand="#0a2c10", rock="#051d08",
    building="#0d3412", building_line="#3fff66",
    minor="#2fd957", glow="#39ff5a", major="#8dff9d", highway="#d6ffd9",
    rail="#39ff5a", boundary="#8dff9d",
    font=["Roboto Regular"], font_bold=["Roboto Bold"], font_italic=["Roboto Italic"],
    transform="none", spacing=0.03, text="#b9ffb9", text_halo="#04200a", halo_w=1.6,
    meta={"overlay": "scanlines"}),
 "sanandreas": dict(name="Great Street Empire: San Andreas",
    bg="#ffffff", landuse="#f3f3f3", green="#7fb069", water="#a9cbea", water_line="#86b4df",
    farmland="#f0f3e8", sand="#f6f0dc", rock="#ebebeb",
    building="#dddddd", building_line="#c4c4c4",
    minor="#1a1a1a", major="#000000", major_casing="#ffffff", highway="#8a7a66",
    rail="#b03030", boundary="#000000",
    font=["Metropolis Bold"], font_bold=["Metropolis Black"], font_italic=["Metropolis Bold Italic"],
    transform="none", spacing=0.02, text="#111111", text_halo="#ffffff", halo_w=1.8, meta={}),

 # ---- Moroccan themes -------------------------------------------------------
 "zellige": dict(name="Zellige",
    # Fès mosaic: cream plaster, cobalt water, emerald gardens, terracotta houses
    bg="#f1e9d6", landuse="#e9dfc6", green="#1f8a6a", water="#1b4f9c", water_line="#163f7d",
    farmland="#ece2c8", sand="#efe3c2", rock="#e3d9c2",
    building="#c9743f", building_line="#8e4a24",
    minor="#ffffff", minor_casing="#1b4f9c", major="#ffffff", major_casing="#163f7d", highway="#e0a52a",
    rail="#163f7d", boundary="#163f7d",
    font=["PT Sans Bold"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"],
    transform="none", spacing=0.03, text="#163f7d", text_halo="#f1e9d6", halo_w=1.6,
    meta={"overlay": "zellige"}),
 "sahara": dict(name="Sahara",
    # dunes at sunset: warm sand, deeper dune folds, turquoise oases, adobe houses
    bg="#e3c58f", landuse="#d9b67c", green="#6f9a5a", water="#3fb6c6", water_line="#2a8f9e",
    farmland="#d8bb84", sand="#edd49c", rock="#c9a673",
    building="#b8773f", building_line="#7c4a22",
    minor="#f6e7c8", minor_casing="#8a5a2b", major="#fff3da", major_casing="#5a3a16", highway="#c7452c",
    rail="#5a3a16", boundary="#5a3a16",
    font=["Roboto Condensed Regular"], font_bold=["Roboto Condensed Bold"], font_italic=["Roboto Condensed Italic"],
    transform="none", spacing=0.04, text="#4a2e12", text_halo="#f1dcae", halo_w=1.4,
    meta={"overlay": "heat"}),
 "medina": dict(name="Medina",
    # Marrakech, the red city: ochre-pink walls, deep red houses, cream lanes, palm green
    bg="#d9a483", landuse="#cf9775", green="#5e8a4a", water="#2a9d8f", water_line="#1f7d72",
    farmland="#d4a07f", sand="#e0b58f", rock="#c08f6e",
    building="#a84a31", building_line="#6e2e1c",
    minor="#f5e6cf", minor_casing="#8a3f2a", major="#fbf1dd", major_casing="#6e2e1c", highway="#f0c76a",
    rail="#6e2e1c", boundary="#6e2e1c",
    font=["Open Sans Semibold"], font_bold=["Open Sans Extra Bold"], font_italic=["Open Sans Italic"],
    transform="none", spacing=0.02, text="#3f1c12", text_halo="#f0d4ba", halo_w=1.5,
    meta={"overlay": "paper"}),
 "chefchaouen": dict(name="Chefchaouen",
    # the blue pearl: washed blue walls, white lanes, indigo water
    bg="#cfe1ee", landuse="#bfd6e8", green="#6fa88f", water="#1f5e8a", water_line="#174a6e",
    farmland="#c7dbe8", sand="#d9e6ee", rock="#b7cad8",
    building="#3f7fbf", building_line="#24568a",
    minor="#ffffff", minor_casing="#6a9ccc", major="#ffffff", major_casing="#24568a", highway="#f2d16b",
    rail="#24568a", boundary="#24568a",
    font=["Metropolis Semi Bold"], font_bold=["Metropolis Extra Bold"], font_italic=["Metropolis Regular Italic"],
    transform="none", spacing=0.03, text="#163a5c", text_halo="#e8f1f8", halo_w=1.6, meta={}),
 "atlas": dict(name="Atlas",
    # High Atlas: pale valley floors, cedar green, bare rock in grey-brown, snow-blue rivers
    bg="#e3e6d8", landuse="#d8dcc9", green="#7aa567", water="#4a90c2", water_line="#3a76a3",
    farmland="#dadec4", sand="#e9e2c8", rock="#b8b0a2",
    building="#8c8378", building_line="#5c554c",
    minor="#ffffff", minor_casing="#9a9a8c", major="#ffffff", major_casing="#5c6b5a", highway="#e5a94b",
    rail="#5c554c", boundary="#4a5548",
    font=["PT Sans Regular"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"],
    transform="none", spacing=0.02, text="#2f3a2c", text_halo="#eef0e8", halo_w=1.5, meta={}),
 "amazigh": dict(name="Amazigh",
    # the flag: sky blue, land green, desert yellow, and the red yaz for the houses
    bg="#f6e9b8", landuse="#efdfa6", green="#2f9a4a", water="#2f6fdb", water_line="#2457b0",
    farmland="#f1e3ad", sand="#f8ecc0", rock="#e3d39e",
    building="#d9271e", building_line="#8e1812",
    minor="#ffffff", minor_casing="#2457b0", major="#ffffff", major_casing="#2457b0", highway="#d9271e",
    rail="#2457b0", boundary="#2457b0",
    font=["Metropolis Bold"], font_bold=["Metropolis Black"], font_italic=["Metropolis Bold Italic"],
    transform="uppercase", spacing=0.06, text="#1a2f5a", text_halo="#f6e9b8", halo_w=1.6, meta={}),
 "ramadan": dict(name="Ramadan Night",
    # deep indigo night, gold-lit boulevards, lanterns on every street
    bg="#121a3a", landuse="#172046", green="#1f3d4a", water="#0a1230", water_line="#2a3f8a",
    farmland="#151d40", sand="#1a2348", rock="#10173a",
    building="#22306a", building_line="#3a4f9a",
    minor="#3f5296", glow="#f2c94c", major="#f5d77a", highway="#ffe9a6",
    rail="#f2c94c", boundary="#f2c94c",
    font=["Open Sans Semibold"], font_bold=["Open Sans Extra Bold"], font_italic=["Open Sans Italic"],
    transform="none", spacing=0.02, text="#f7e7b0", text_halo="#0b1030", halo_w=1.6,
    meta={"overlay": "stars"}),
 "essaouira": dict(name="Essaouira",
    # whitewashed walls, blue doors, Atlantic wind: white houses outlined in blue
    bg="#f4f1ea", landuse="#ebe7dc", green="#8fb59a", water="#2b7fb3", water_line="#1f6490",
    farmland="#ece8d9", sand="#f1e7cc", rock="#d9d5c8",
    building="#fdfdfb", building_line="#2b7fb3",
    minor="#d7e6ee", major="#ffffff", major_casing="#2b7fb3", highway="#1f6490",
    rail="#1f6490", boundary="#1f6490",
    font=["Roboto Regular"], font_bold=["Roboto Bold"], font_italic=["Roboto Italic"],
    transform="none", spacing=0.03, text="#1f4a66", text_halo="#ffffff", halo_w=1.6, meta={}),
 "tafraout": dict(name="Tafraout",
    # pink granite of the Anti-Atlas, argan green, and the famous painted blue rocks
    bg="#e8c9b6", landuse="#dfbca7", green="#7a9a63", water="#4fa3b5", water_line="#3b8294",
    farmland="#e3c1ab", sand="#eed7c2", rock="#c98f7a",
    building="#5b7fcf", building_line="#3a5aa0",
    minor="#fbeee4", minor_casing="#a6705c", major="#fff6ee", major_casing="#7c4a3c", highway="#d9775a",
    rail="#7c4a3c", boundary="#7c4a3c",
    font=["Roboto Condensed Regular"], font_bold=["Roboto Condensed Bold"], font_italic=["Roboto Condensed Italic"],
    transform="none", spacing=0.04, text="#4a2a22", text_halo="#f6e3d6", halo_w=1.4,
    meta={"overlay": "heat"}),

 # ---- more Moroccan places and things -----------------------------------
 "minttea": dict(name="Mint Tea",
    # fresh mint, gold-rimmed glasses: pale mint ground, gold houses, green-edged lanes
    bg="#e6f2e8", landuse="#d9ebdc", green="#5fae7a", water="#8fd1c8", water_line="#4fa89c",
    farmland="#dfeede", sand="#eef3e2", rock="#cfdccf",
    building="#c9a45c", building_line="#8f6f2e",
    minor="#ffffff", minor_casing="#9cc7a8", major="#ffffff", major_casing="#3f8a5c", highway="#e0b84a",
    rail="#3f8a5c", boundary="#2f6a46",
    font=["Open Sans Regular"], font_bold=["Open Sans Bold"], font_italic=["Open Sans Italic"],
    transform="none", spacing=0.03, text="#1f4a30", text_halo="#f1f8f2", halo_w=1.5),
 "argan": dict(name="Argan",
    # the Souss: olive argan groves, honey-coloured houses, warm straw ground
    bg="#e9d9b4", landuse="#e0cd9f", green="#8a9a4e", water="#6fb3c3", water_line="#4a8e9e",
    farmland="#e3cf9e", sand="#efe0bb", rock="#c9b283",
    building="#b07a3a", building_line="#6e4a1e",
    minor="#fff6e0", minor_casing="#a8884e", major="#fffaf0", major_casing="#6e4a1e", highway="#c9602a",
    rail="#6e4a1e", boundary="#6e4a1e",
    font=["PT Sans Regular"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"],
    transform="none", spacing=0.02, text="#4a3414", text_halo="#f3e8c8", halo_w=1.4,
    meta={"overlay": "heat"}),
 "ifrane": dict(name="Ifrane",
    # snow: white ground, dark cedar blocks, wooden chalets, blue shadows on the slopes
    bg="#f4f7fa", landuse="#eaeff4", green="#2f5f3f", water="#9cc4e8", water_line="#6a9fcc",
    farmland="#eef2f6", sand="#f6f8fa", rock="#d6dde5",
    building="#8b5e3c", building_line="#5a3b22", extrude_forest=True,
    minor="#ffffff", minor_casing="#b9c6d3", major="#ffffff", major_casing="#6d7f92", highway="#dfe7ef",
    rail="#5a6a7a", boundary="#5a6a7a",
    font=["Roboto Regular"], font_bold=["Roboto Bold"], font_italic=["Roboto Italic"],
    transform="none", spacing=0.03, text="#2b3a4a", text_halo="#ffffff", halo_w=1.6,
    shade="#9fb4c8", highlight="#ffffff", sky="#cfe3f5", horizon="#ffffff"),
 "dakhla": dict(name="Dakhla",
    # the lagoon: turquoise water, pale dune sand, white camp houses, kite orange highways
    bg="#efe3c6", landuse="#e8dab8", green="#8fb87a", water="#36c6c0", water_line="#1f9f9a",
    farmland="#ece0c0", sand="#f5ead0", rock="#d8c8a4",
    building="#f4f0e6", building_line="#8a7f6a",
    minor="#ffffff", minor_casing="#c4b08a", major="#ffffff", major_casing="#7a6a4a", highway="#ff9a3c",
    rail="#7a6a4a", boundary="#7a6a4a",
    font=["Metropolis Medium"], font_bold=["Metropolis Bold"], font_italic=["Metropolis Medium Italic"],
    transform="none", spacing=0.03, text="#2b3a3a", text_halo="#f7f1e2", halo_w=1.5,
    sky="#7cc8f0", horizon="#e6f4fb"),
 "caftan": dict(name="Caftan",
    # royal purple velvet with gold embroidery: gold-lit roads, magenta houses
    bg="#3b1f4e", landuse="#44255a", green="#2e4a4a", water="#1e1236", water_line="#c89b3c",
    farmland="#3f2254", sand="#4a2b60", rock="#331a44",
    building="#7a3b8a", building_line="#e6b85c",
    minor="#9a6cae", glow="#e6b85c", major="#f3d27a", highway="#fff0b8",
    rail="#e6b85c", boundary="#e6b85c",
    font=["Metropolis Semi Bold"], font_bold=["Metropolis Black"], font_italic=["Metropolis Regular Italic"],
    transform="none", spacing=0.04, text="#f7e6b8", text_halo="#2a1238", halo_w=1.6,
    sky="#1a0a2a", horizon="#5a2f74"),

 # ---- classic cartography looks -------------------------------------------
 "blueprint": dict(name="Blueprint",
    # engineering drawing: deep blue paper, white ink, uppercase condensed lettering
    bg="#0d3b8c", landuse="#0f42a0", green="#0f4a8f", water="#082a6a", water_line="#9fd0ff",
    farmland="#0e3f95", sand="#114a9c", rock="#0b3380",
    building="#1a55b8", building_line="#dfe9ff",
    minor="#bcd2ff", major="#ffffff", highway="#ffffff",
    rail="#dfe9ff", boundary="#dfe9ff",
    font=["Roboto Condensed Regular"], font_bold=["Roboto Condensed Bold"], font_italic=["Roboto Condensed Italic"],
    transform="uppercase", spacing=0.08, text="#eaf2ff", text_halo="#0d3b8c", halo_w=1.4,
    sky="#0a1f4d", horizon="#1a4fb0", shade="#061f4d", highlight="#5f8fe0"),
 "sketch": dict(name="Pencil Sketch",
    # hand-drawn on cream paper: grey pencil lines, soft washes, outlined houses
    bg="#f7f3ea", landuse="#f1ece0", green="#dfe6cf", water="#dbe7ee", water_line="#8da3ad",
    farmland="#f3eedf", sand="#f3eddc", rock="#e8e3d6",
    building="#e9e3d5", building_line="#6b6560",
    minor="#ffffff", minor_casing="#8a8580", major="#ffffff", major_casing="#4d4945", highway="#f0e9d8",
    rail="#6b6560", boundary="#6b6560",
    font=["PT Sans Caption Regular"], font_bold=["PT Sans Caption Web Bold"], font_italic=["PT Sans Italic"],
    transform="none", spacing=0.02, text="#3b3733", text_halo="#f7f3ea", halo_w=1.4,
    meta={"overlay": "paper"}),
 "noir": dict(name="Noir",
    # pure black and white, high contrast
    bg="#000000", landuse="#0a0a0a", green="#141414", water="#1e1e1e", water_line="#5a5a5a",
    farmland="#070707", sand="#0c0c0c", rock="#111111",
    building="#2a2a2a", building_line="#8a8a8a",
    minor="#9a9a9a", major="#ffffff", major_casing="#000000", highway="#ffffff",
    rail="#8a8a8a", boundary="#ffffff",
    font=["Roboto Bold"], font_bold=["Roboto Black"], font_italic=["Roboto Italic"],
    transform="none", spacing=0.03, text="#ffffff", text_halo="#000000", halo_w=2,
    sky="#000000", horizon="#2a2a2a", shade="#000000", highlight="#6a6a6a"),
}
import copy
STYLES_DIR = r"C:\Users\sabri\Desktop\My Map\styles"   # Docker tile server (tileserver-gl)

def server_variant(style):
    """Same look, but fed from the local morocco.mbtiles and local fonts, so
    tileserver-gl can rasterise it to PNG tiles."""
    s = copy.deepcopy(style)
    s["sources"] = {"osm": {"type": "vector", "url": "mbtiles://{morocco}"}}
    s["glyphs"] = "{fontstack}/{range}.pbf"
    s.pop("sprite", None)          # no icons used; avoids a missing-sprite error
    s.pop("metadata", None)        # playground-only hints
    s.pop("terrain", None)         # flat PNG tiles: no 3D terrain, sky or hillshade
    s.pop("sky", None)
    s["layers"] = [l for l in s["layers"] if l.get("source") != "dem" and "icon-image" not in l.get("layout", {})]
    return s

# ---- One skin per Moroccan city. Selecting it flies to the city. -------------
def city(name, lng, lat, zoom, **t):
    t.setdefault("font", ["Open Sans Semibold"]); t.setdefault("font_bold", ["Open Sans Extra Bold"])
    t.setdefault("font_italic", ["Open Sans Italic"])
    t.setdefault("transform", "none"); t.setdefault("spacing", 0.02); t.setdefault("halo_w", 1.5)
    t.setdefault("farmland", _mix(t["bg"], t["green"], 0.25)); t.setdefault("sand", _mix(t["bg"], "#ffffff", 0.2))
    t.setdefault("rock", _mix(t["bg"], "#000000", 0.12))
    m = t.setdefault("meta", {}); m.update(center=[lng, lat], zoom=zoom, city=name)
    t["name"] = "City: " + name
    return t

def _hex(c): return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
def _mix(c, to, f):
    a, b = _hex(c), _hex(to)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * f) for x, y in zip(a, b))

CITY_THEMES = {
 "casablanca": city("Casablanca", -7.6180, 33.5935, 15.5,
    # Art Deco white, Atlantic blue, the green-tiled roofs of Hassan II
    bg="#eef0f2", landuse="#e4e7ea", green="#3f9a7a", water="#2563a8", water_line="#1b4e86",
    building="#ffffff", building_line="#8e9aa6",
    minor="#ffffff", minor_casing="#aab6c2", major="#ffffff", major_casing="#4a5d70", highway="#2f8f7a",
    rail="#4a5d70", boundary="#4a5d70", text="#1f2f3f", text_halo="#ffffff",
    font=["Metropolis Semi Bold"], font_bold=["Metropolis Black"], font_italic=["Metropolis Regular Italic"]),
 "rabat": city("Rabat", -6.8350, 34.0210, 15,
    # Oudayas: blue-and-white kasbah, Hassan tower ochre, green capital gardens
    bg="#f3efe6", landuse="#ebe6da", green="#5f9e6a", water="#2b6cb0", water_line="#1f528a",
    building="#ffffff", building_line="#2b6cb0",
    minor="#ffffff", minor_casing="#9bb5d0", major="#ffffff", major_casing="#2b4a6b", highway="#c9973b",
    rail="#2b4a6b", boundary="#2b4a6b", text="#1f3550", text_halo="#f7f4ec"),
 "fes": city("Fès", -4.9760, 34.0655, 15.3,
    # the old medina: ochre walls, Fès green roofs, tannery browns
    bg="#e9dcc2", landuse="#dfd0b0", green="#2f7a5a", water="#4a8fa8", water_line="#357388",
    building="#c99a5b", building_line="#7a5a2a",
    minor="#f7eedb", minor_casing="#9a7a4a", major="#fdf6e8", major_casing="#5a3f1e", highway="#2f7a5a",
    rail="#5a3f1e", boundary="#5a3f1e", text="#3f2a12", text_halo="#f3e8d0",
    font=["PT Sans Regular"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"], meta={"overlay": "paper"}),
 "tanger": city("Tanger", -5.8102, 35.7800, 15,
    # the strait: white houses, Mediterranean turquoise, deep blue sea, pastel medina
    bg="#f4f6f3", landuse="#eaeee8", green="#78b08a", water="#1f77b4", water_line="#15598a",
    building="#ffffff", building_line="#6a8aa0",
    minor="#ffffff", minor_casing="#b8c9d4", major="#ffffff", major_casing="#3f5f74", highway="#f2b84b",
    rail="#3f5f74", boundary="#3f5f74", text="#1e3a4c", text_halo="#ffffff",
    font=["Roboto Regular"], font_bold=["Roboto Bold"], font_italic=["Roboto Italic"]),
 "agadir": city("Agadir", -9.5981, 30.4278, 14.8,
    # beach sand, surf blue, modern white, sunset orange highways
    bg="#f6ecd8", landuse="#efe3c8", green="#8fbf7a", water="#2fa7d6", water_line="#1f85ad",
    building="#ffffff", building_line="#c0a884",
    minor="#ffffff", minor_casing="#d2bf9c", major="#ffffff", major_casing="#8a6e45", highway="#ff8c42",
    rail="#8a6e45", boundary="#8a6e45", text="#4a3a22", text_halo="#fbf4e6",
    font=["Metropolis Medium"], font_bold=["Metropolis Bold"], font_italic=["Metropolis Medium Italic"]),
 "meknes": city("Meknès", -5.5547, 33.8935, 15,
    # imperial city: Bab Mansour green and gold, olive groves, ochre ramparts
    bg="#ece4cf", landuse="#e2d9bf", green="#6b8f3e", water="#4f8fa6", water_line="#3a7086",
    building="#b8955a", building_line="#6e5424",
    minor="#fbf5e6", minor_casing="#a08a5a", major="#fffaf0", major_casing="#4e5a2a", highway="#c9a227",
    rail="#4e5a2a", boundary="#4e5a2a", text="#33401a", text_halo="#f3eddc",
    font=["PT Sans Regular"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"]),
 "tetouan": city("Tétouan", -5.3684, 35.5785, 15.5,
    # the white dove: Andalusian white, green shutters, Rif green hills
    bg="#f7f8f6", landuse="#eef0ec", green="#5fa06e", water="#3b8fc4", water_line="#2a709c",
    building="#ffffff", building_line="#3f7a4e",
    minor="#ffffff", minor_casing="#b9c9bc", major="#ffffff", major_casing="#355d3e", highway="#dfa73b",
    rail="#355d3e", boundary="#355d3e", text="#1f3a26", text_halo="#ffffff"),
 "oujda": city("Oujda", -1.9086, 34.6814, 15,
    # eastern gateway: terracotta, olive, desert ochre, Algerian border dashes
    bg="#ecdfc8", landuse="#e3d4b8", green="#7f9a4f", water="#5a9bb0", water_line="#427a8c",
    building="#c47a4a", building_line="#7a4424",
    minor="#fbf3e4", minor_casing="#ad8d64", major="#fff8ec", major_casing="#6a4a2a", highway="#b44a2a",
    rail="#6a4a2a", boundary="#6a4a2a", text="#4a2e18", text_halo="#f5ebd8",
    font=["Roboto Condensed Regular"], font_bold=["Roboto Condensed Bold"], font_italic=["Roboto Condensed Italic"]),
 "ouarzazate": city("Ouarzazate", -6.8936, 30.9189, 14.8,
    # door of the desert: red-earth kasbahs, film-set sand, dark palm green
    bg="#e3c6a2", landuse="#d9b88f", green="#4f7a3a", water="#4aa3b8", water_line="#2f8295",
    building="#a6532e", building_line="#5e2c14",
    minor="#f6e6cf", minor_casing="#8c5a3a", major="#fdf0dc", major_casing="#5e2c14", highway="#e08a3c",
    rail="#5e2c14", boundary="#5e2c14", text="#3f1f0e", text_halo="#f2dfc4",
    font=["Roboto Condensed Regular"], font_bold=["Roboto Condensed Bold"], font_italic=["Roboto Condensed Italic"],
    meta={"overlay": "heat"}),
 "eljadida": city("El Jadida", -8.5008, 33.2549, 15.2,
    # Portuguese ramparts: grey stone, sea green, white medina
    bg="#eceeea", landuse="#e2e5e0", green="#7aa884", water="#2f8a8a", water_line="#226b6b",
    building="#f4f4f0", building_line="#6f7a78",
    minor="#ffffff", minor_casing="#b4bcb8", major="#ffffff", major_casing="#4a5654", highway="#c99a3b",
    rail="#4a5654", boundary="#4a5654", text="#283432", text_halo="#f7f8f6",
    font=["PT Sans Regular"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"]),
 "laayoune": city("Laâyoune", -13.2033, 27.1536, 14.5,
    # Saharan capital: pale ochre, white houses, Saguia el-Hamra green strip
    bg="#efe2c4", landuse="#e6d7b3", green="#9bb36a", water="#52b0c8", water_line="#3a8ea3",
    building="#fbf7ec", building_line="#a48a5c",
    minor="#ffffff", minor_casing="#c9b58a", major="#ffffff", major_casing="#7a6440", highway="#d9822b",
    rail="#7a6440", boundary="#7a6440", text="#4a3a1e", text_halo="#f7efdc",
    font=["Metropolis Medium"], font_bold=["Metropolis Bold"], font_italic=["Metropolis Medium Italic"],
    meta={"overlay": "heat"}),
 "kenitra": city("Kénitra", -6.5802, 34.2610, 15,
    # the Sebou and the Gharb plain: river green, wet farmland, brick houses
    bg="#e8efe0", landuse="#dfe8d4", green="#5f9f4a", water="#3f86a8", water_line="#2d6a88",
    building="#b86a4a", building_line="#73402a",
    minor="#ffffff", minor_casing="#a9bda0", major="#ffffff", major_casing="#3f5f3a", highway="#d49a2a",
    rail="#3f5f3a", boundary="#3f5f3a", text="#243a22", text_halo="#f1f6ec"),
 "safi": city("Safi", -9.2372, 32.2994, 15,
    # pottery city: glaze blue, kiln ochre, Atlantic grey-green
    bg="#efe6d6", landuse="#e6dcc8", green="#7faa7a", water="#3f7f9f", water_line="#2d6280",
    building="#3f6fb0", building_line="#1f4278",
    minor="#fbf6ec", minor_casing="#b89a6e", major="#fffaf2", major_casing="#5a4420", highway="#d4862a",
    rail="#5a4420", boundary="#5a4420", text="#2f2a1a", text_halo="#f6efe2",
    font=["PT Sans Regular"], font_bold=["PT Sans Bold"], font_italic=["PT Sans Italic"]),
 "nador": city("Nador", -2.9287, 35.1740, 14.5,
    # Marchica lagoon: lagoon teal, Rif green, white houses, Mediterranean blue
    bg="#f1f3ee", landuse="#e7eae2", green="#6ea873", water="#2bb5b0", water_line="#1e8f8b",
    building="#ffffff", building_line="#7a8e8a",
    minor="#ffffff", minor_casing="#b6c4c0", major="#ffffff", major_casing="#3e5a56", highway="#e3a23a",
    rail="#3e5a56", boundary="#3e5a56", text="#1f3532", text_halo="#f8faf7"),
 "benimellal": city("Béni Mellal", -6.3498, 32.3373, 15,
    # orange groves at the foot of the Middle Atlas: orange, leaf green, Atlas grey
    bg="#eef0e4", landuse="#e5e8d8", green="#4f9a3f", water="#4a94b8", water_line="#357598",
    building="#e0863a", building_line="#8e4f1a",
    minor="#ffffff", minor_casing="#aebf9f", major="#ffffff", major_casing="#4a5a3a", highway="#e0863a",
    rail="#4a5a3a", boundary="#4a5a3a", text="#2a3a20", text_halo="#f5f7ef"),
}
THEMES.update(CITY_THEMES)

# ---- One skin per country, coloured from its flag. ---------------------------
import colorsys
def _hsl(c):
    r, g, b = (x / 255 for x in _hex(c)); h, l, s = colorsys.rgb_to_hls(r, g, b); return h * 360, s, l
def _is_white(c): h, s, l = _hsl(c); return l > 0.85 and s < 0.25
def _is_black(c):
    # true black or near-black greys only; a dark saturated green or navy is a real flag colour
    h, s, l = _hsl(c); return l < 0.12 or (l < 0.25 and s < 0.3)
def _hue_in(c, lo, hi): h, s, l = _hsl(c); return s > 0.25 and lo <= h <= hi

def country(rec):
    cols = [h for h, share in rec["colours"]] or ["#9a9a9a"]
    chroma = [c for c in cols if not _is_white(c) and not _is_black(c)]
    c1 = cols[0]
    # ground: a pale tint of the dominant colour
    if _is_white(c1): bg = "#f4f4f1"
    elif _is_black(c1): bg = "#e4e4e8"
    else: bg = _mix(c1, "#ffffff", 0.78)
    # houses: the second colour of the flag; roads: the third; outlines: the darkest
    others = [c for c in chroma if c != c1] or chroma or ["#8a8a8a"]
    building = others[0]
    highway = others[1] if len(others) > 1 else (c1 if c1 in chroma else building)
    dark = min(cols + ["#555555"], key=lambda c: _hsl(c)[2])
    casing = dark if _hsl(dark)[2] < 0.45 else _mix(dark, "#000000", 0.5)
    blue = next((c for c in chroma if _hue_in(c, 190, 260)), None)
    green = next((c for c in chroma if _hue_in(c, 80, 170)), None)
    t = dict(
        bg=bg, landuse=_mix(bg, "#000000", 0.05),
        green=_mix(green, "#ffffff", 0.3) if green else "#a9c9a0",
        water=_mix(blue, "#ffffff", 0.3) if blue else "#9cc7e6",
        water_line=blue or "#5f9dc8",
        building=building, building_line=_mix(building, "#000000", 0.45),
        minor="#ffffff", minor_casing=_mix(casing, "#ffffff", 0.55),
        major="#ffffff", major_casing=casing, highway=highway,
        rail=casing, boundary=casing,
        text=_mix(casing, "#000000", 0.3), text_halo=_mix(bg, "#ffffff", 0.5),
        font=["Open Sans Semibold"], font_bold=["Open Sans Extra Bold"], font_italic=["Open Sans Italic"],
        transform="none", spacing=0.02, halo_w=1.5,
        farmland=_mix(bg, green or "#a9c9a0", 0.2), sand=_mix(bg, "#ffffff", 0.2), rock=_mix(bg, "#000000", 0.12),
        meta={"center": rec["center"], "zoom": rec["zoom"], "city": rec["capital"] or rec["name"],
              "pitch": 55 if rec["zoom"] > 10 else 35, "bearing": -20},
        name="Country: " + rec["name"] + (f" ({rec['name_fr']})" if rec["name_fr"] != rec["name"] else ""),
        group="Countries",
    )
    return t

COUNTRY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "countries_palette.json")
COUNTRY_THEMES = {}
if os.path.exists(COUNTRY_FILE):
    for rec in json.load(open(COUNTRY_FILE, encoding="utf-8")):
        COUNTRY_THEMES["c-" + rec["code"]] = country(rec)
# home coordinates for the place skins that already exist
for k, (lng, lat, zoom, nm) in {"medina": (-7.9890, 31.6280, 15.3, "Marrakech"),
                                "chefchaouen": (-5.2636, 35.1688, 15.2, "Chefchaouen"),
                                "essaouira": (-9.7700, 31.5120, 15.3, "Essaouira"),
                                "tafraout": (-8.9750, 29.7210, 14.8, "Tafraout"),
                                "ifrane": (-5.1070, 33.5270, 14.6, "Ifrane"),
                                "dakhla": (-15.9300, 23.7200, 12.5, "Dakhla"),
                                "atlas": (-7.9200, 31.1400, 13.2, "Imlil"),
                                "sahara": (-4.0200, 31.1000, 12.3, "Merzouga")}.items():
    THEMES[k].setdefault("meta", {}).update(center=[lng, lat], zoom=zoom, city=nm)
# relief is derived from atlas further down and inherits its home

THEMES.update(COUNTRY_THEMES)   # countries get the same 3D defaults as everything else

# ---- Every skin is 3D: real terrain, hillshade, extruded houses, tilted camera.
def _dark(c): r, g, b = _hex(c); return (0.299 * r + 0.587 * g + 0.114 * b) < 100

for key, t in THEMES.items():
    t.setdefault("extrude", True)
    t.setdefault("terrain", True)
    t.setdefault("exaggeration", 1.2)
    t.setdefault("hillshade", 0.4)
    t.setdefault("shade", _mix(t["bg"], "#000000", 0.6))
    t.setdefault("highlight", _mix(t["bg"], "#ffffff", 0.9))
    t.setdefault("fog", t["bg"])
    if _dark(t["bg"]):
        t.setdefault("sky", "#0a0f2a"); t.setdefault("horizon", _mix(t["bg"], "#ffffff", 0.2))
    else:
        t.setdefault("sky", "#8fbce6"); t.setdefault("horizon", _mix(t["bg"], "#ffffff", 0.4))
    meta = t.setdefault("meta", {})
    meta.setdefault("pitch", 55); meta.setdefault("bearing", -20)

# per-skin tuning on top of the defaults
THEMES["cubeworld"].update(extrude_forest=True, exaggeration=1.5, hillshade=0.35,
                           sky="#79b8ff", horizon="#cfe8ff", shade="#2f3a22")
THEMES["cybershock"].update(hillshade=0.5, sky="#1a0a2a", horizon="#6c1a35", shade="#2a0613", highlight="#ff6fa0")
THEMES["sahara"].update(exaggeration=1.6, hillshade=0.55, sky="#f3c98a", horizon="#f7dfae",
                        shade="#5a3a16", highlight="#fff2d0")
THEMES["sahara"]["meta"].update(bearing=-30)
THEMES["medina"].update(extrude_forest=True, hillshade=0.45, sky="#f2b58a", horizon="#f6d7bd",
                        shade="#5a2416", highlight="#ffe6d2")
THEMES["ramadan"].update(hillshade=0.6, sky="#0a0f2a", horizon="#2a2f6a", shade="#05081c", highlight="#3a4f9a")
# the High Atlas is steep already: keep exaggeration low and the tilt moderate,
# or the camera ends up inside a mountain in deep valleys
THEMES["atlas"].update(exaggeration=1.15, hillshade=0.5, shade="#3a2e1e")
THEMES["atlas"]["meta"].update(pitch=50, bearing=-25)
THEMES["relief"] = {**THEMES["atlas"], "name": "Relief (Atlas + forests)", "extrude_forest": True,
                    "meta": dict(THEMES["atlas"]["meta"])}

# ---- Earth: satellite imagery on a globe, with roads and names drawn over it
SAT = {"type": "raster", "tileSize": 256, "maxzoom": 19,
       "tiles": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
       "attribution": "Imagery © Esri, Maxar, Earthstar Geographics"}

def build_earth():
    white = {"text-color": "#ffffff", "text-halo-color": "#000000", "text-halo-width": 1.4, "text-halo-blur": 0.5}
    font = ["Roboto Regular"]; bold = ["Roboto Bold"]
    name = ["coalesce", ["get", "name:fr"], ["get", "name"]]
    round_ = {"line-cap": "round", "line-join": "round"}
    L = [
        {"id": "background", "type": "background", "paint": {"background-color": "#0b1b33"}},
        {"id": "satellite", "type": "raster", "source": "sat",
         "paint": {"raster-saturation": 0.05, "raster-contrast": 0.05}},
        {"id": "hillshade", "type": "hillshade", "source": "dem", "maxzoom": 12,
         "paint": {"hillshade-exaggeration": 0.2, "hillshade-shadow-color": "#000000",
                   "hillshade-highlight-color": "#ffffff", "hillshade-accent-color": "#000000"}},
        # houses in 3D: pale, slightly see-through so the rooftops in the imagery still show
        {"id": "building", "type": "fill-extrusion", "source": "osm", "source-layer": "building",
         "minzoom": 14,
         "paint": {"fill-extrusion-color": "#e8e2d6",
                   "fill-extrusion-height": ["coalesce", ["get", "render_height"], 8],
                   "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
                   "fill-extrusion-opacity": 0.8,
                   "fill-extrusion-vertical-gradient": True}},
        {"id": "road-minor", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 13, "filter": MINOR, "layout": round_,
         "paint": {"line-color": "#ffffff", "line-opacity": 0.55, "line-width": z(13, 0.6, 17, 2.5)}},
        {"id": "road-major", "type": "line", "source": "osm", "source-layer": "transportation",
         "minzoom": 7, "filter": MAJOR, "layout": round_,
         "paint": {"line-color": "#ffe29a", "line-opacity": 0.8, "line-width": z(7, 0.6, 12, 1.4, 16, 4)}},
        {"id": "road-highway", "type": "line", "source": "osm", "source-layer": "transportation",
         "filter": HIGHWAY, "layout": round_,
         "paint": {"line-color": "#ffcc55", "line-opacity": 0.9, "line-width": z(4, 0.6, 10, 1.6, 16, 5)}},
        {"id": "boundary-country", "type": "line", "source": "osm", "source-layer": "boundary",
         "filter": ["all", ["==", "admin_level", 2], ["!=", "disputed", 1], ["!=", "maritime", 1]],
         "paint": {"line-color": "#ffffff", "line-opacity": 0.7, "line-width": z(2, 0.6, 10, 1.8),
                   "line-dasharray": [4, 2]}},
        {"id": "road-label", "type": "symbol", "source": "osm", "source-layer": "transportation_name",
         "minzoom": 14, "filter": ["!=", "class", "rail"],
         "layout": {"text-font": font, "symbol-placement": "line", "text-field": name, "text-size": 11},
         "paint": white},
        {"id": "poi-label", "type": "symbol", "source": "osm", "source-layer": "poi",
         "minzoom": 15, "filter": ["all", ["has", "name"], ["<=", "rank", 14]],
         "layout": {"text-font": font, "text-field": name, "text-size": 10, "text-max-width": 8,
                    "text-anchor": "top", "text-offset": [0, 0.4], "text-optional": True},
         "paint": white},
        {"id": "place-village", "type": "symbol", "source": "osm", "source-layer": "place",
         "minzoom": 9, "filter": ["in", "class", "village", "hamlet", "suburb", "neighbourhood", "quarter"],
         "layout": {"text-font": font, "text-field": name, "text-size": z(9, 9, 14, 12)}, "paint": white},
        {"id": "place-town", "type": "symbol", "source": "osm", "source-layer": "place",
         "minzoom": 6, "filter": ["==", "class", "town"],
         "layout": {"text-font": font, "text-field": name, "text-size": z(6, 9, 14, 14)}, "paint": white},
        {"id": "place-city", "type": "symbol", "source": "osm", "source-layer": "place",
         "filter": ["==", "class", "city"],
         "layout": {"text-font": bold, "text-field": name, "text-size": z(3, 10, 12, 20)}, "paint": white},
        {"id": "place-country", "type": "symbol", "source": "osm", "source-layer": "place",
         "maxzoom": 7, "filter": ["==", "class", "country"],
         "layout": {"text-font": bold, "text-field": name, "text-size": z(1, 10, 6, 18),
                    "text-transform": "uppercase", "text-letter-spacing": 0.15}, "paint": white},
    ]
    return {"version": 8, "name": "Earth", "projection": {"type": "globe"},
            "metadata": {"playground": {"globe": True, "pitch": 55, "bearing": -20}},
            "sources": {**SRC, "sat": SAT, "dem": DEM}, "glyphs": GLYPHS, "sprite": SPRITE,
            "terrain": {"source": "dem", "exaggeration": 1.2},
            "sky": {"sky-color": "#06101f", "horizon-color": "#1e3a5f", "fog-color": "#0b1b33",
                    "sky-horizon-blend": 0.5, "horizon-fog-blend": 0.5, "fog-ground-blend": 0.5,
                    "atmosphere-blend": 0.9},
            "layers": L}


def add_font_fallback(style):
    """Every label asks for the skin's font first and Noto Sans second, so names
    in Arabic, Chinese or any script the skin font lacks still render."""
    for l in style["layers"]:
        tf = l.get("layout", {}).get("text-font")
        if not isinstance(tf, list) or not tf or not all(isinstance(x, str) for x in tf): continue
        if any(x.startswith("Noto Sans") for x in tf): continue
        heavy = any(w in tf[0] for w in ("Bold", "Black", "Semi", "Extra", "Medium"))
        l["layout"]["text-font"] = tf + ["Noto Sans Bold" if heavy else "Noto Sans Regular"]
    return style

index = []   # finished skins first; the bare starter style goes last
os.makedirs(os.path.join(OUT, "country"), exist_ok=True)
def group_of(t):
    if t.get("group"): return t["group"]
    return "Moroccan cities" if t["name"].startswith("City:") else "Themes"
for key, t in THEMES.items():
    style = add_font_fallback(build(t))
    if group_of(t) == "Countries":
        # many files, no Docker variant (the tile server only holds Morocco data)
        rel = f"country/{key[2:]}.json"
        with open(os.path.join(OUT, rel), "w", encoding="utf-8") as f:
            json.dump(style, f, separators=(",", ":"), ensure_ascii=False)
        index.append({"id": key, "name": t["name"], "file": "skins/" + rel, "group": "Countries"})
        continue
    path = os.path.join(OUT, key + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(style, f, indent=2, ensure_ascii=False)
    index.append({"id": key, "name": t["name"], "file": f"skins/{key}.json", "group": group_of(t)})
    print("wrote", path)
    sdir = os.path.join(STYLES_DIR, key)
    os.makedirs(sdir, exist_ok=True)
    with open(os.path.join(sdir, "style.json"), "w", encoding="utf-8") as f:
        json.dump(server_variant(style), f, indent=2, ensure_ascii=False)
    print("wrote", os.path.join(sdir, "style.json"))
with open(os.path.join(OUT, "earth.json"), "w", encoding="utf-8") as f:
    json.dump(add_font_fallback(build_earth()), f, indent=2, ensure_ascii=False)
index.append({"id": "earth", "name": "Earth (satellite globe)", "file": "skins/earth.json", "group": "Themes"})
print("wrote", os.path.join(OUT, "earth.json"))
index.append({"id": "mine", "name": "My style (starter, 4 layers)", "file": "style.json", "group": "Mine"})
# order the dropdown: Moroccan cities, themes, countries, mine
order = {"Moroccan cities": 0, "Themes": 1, "Countries": 2, "Mine": 3}
index.sort(key=lambda e: order.get(e.get("group", "Themes"), 1))
print(len([e for e in index if e.get("group") == "Countries"]), "country skins")
with open(os.path.join(os.path.dirname(OUT), "skins.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2)
print("wrote skins.json")
