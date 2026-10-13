"""Tiny static server for the playground.

- no-cache headers, so the browser always sees your latest style
- serves the parent project's downloaded fonts at /fonts/
- when it serves a style (*.json), it rewrites "/fonts/..." into the full
  "http://<this host>/fonts/..." so the style also works when another app
  (for example naviq) loads it by URL
- CORS open, for the same reason

Run:  python serve.py  [port]"""
import http.server, os, sys, urllib.parse, subprocess, tempfile, json

# ---- minimal protobuf for the glyph format (glyphs.proto) --------------------
def _varint(b, i):
    r, sh = 0, 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << sh; sh += 7
        if c < 0x80: return r, i
def _fields(b):
    """yield (field_number, wire_type, value) for one message; value is bytes for
    length-delimited fields, int for varints"""
    i = 0
    while i < len(b):
        key, i = _varint(b, i); fn, wt = key >> 3, key & 7
        if wt == 0: v, i = _varint(b, i)
        elif wt == 2: n, i = _varint(b, i); v = b[i:i + n]; i += n
        elif wt == 5: v = b[i:i + 4]; i += 4
        elif wt == 1: v = b[i:i + 8]; i += 8
        else: raise ValueError("wire type %d" % wt)
        yield fn, wt, v
def _enc_varint(n):
    out = bytearray()
    while True:
        c = n & 0x7f; n >>= 7
        out.append(c | 0x80 if n else c)
        if not n: return bytes(out)
def _ld(fn, data): return _enc_varint((fn << 3) | 2) + _enc_varint(len(data)) + data
def merge_glyphs(pbfs, stack_name, rng):
    glyphs, seen = [], set()
    for pbf in pbfs:                       # first font wins, later fonts fill gaps
        for fn, wt, stack in _fields(pbf):
            if fn != 1: continue
            for gfn, gwt, g in _fields(stack):
                if gfn != 3: continue
                gid = next((v for f2, w2, v in _fields(g) if f2 == 1), None)
                if gid is None or gid in seen: continue
                seen.add(gid); glyphs.append(g)
    stack = _ld(1, stack_name.encode()) + _ld(2, rng.encode()) + b"".join(_ld(3, g) for g in glyphs)
    return _ld(1, stack)

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3030
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
# guillaumemeyer/watermarks-remover (MIT), cloned into tools/: strips C2PA, EXIF,
# XMP and AI-provenance metadata from files, and invisible Unicode from text.
CLEANER = os.path.join(HERE, "tools", "watermarks-remover", "service", "scripts", "clean_file.py")
os.chdir(HERE)

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = super().translate_path(path)
        parts = os.path.relpath(local, HERE).split(os.sep)
        if parts[0] == "fonts":                      # /fonts/... -> ../fonts/...
            return os.path.join(FONTS, *parts[1:])
        return local

    def do_GET(self):
        clean = self.path.split("?", 1)[0]
        if clean.startswith("/fonts/") and clean.endswith(".pbf") and "," in urllib.parse.unquote(clean):
            # a font stack like "Metropolis Bold,Noto Sans Regular": merge the glyph
            # files so the first font is used where it has the glyph, the next
            # font fills the gaps (Arabic, Chinese, symbols...). tileserver-gl
            # does the same; here it is a few lines of protobuf surgery.
            stack, rng = urllib.parse.unquote(clean)[len("/fonts/"):].rsplit("/", 1)
            parts = []
            for name in stack.split(","):
                f = os.path.join(FONTS, name.strip(), rng)
                if os.path.isfile(f):
                    with open(f, "rb") as fh: parts.append(fh.read())
            body = merge_glyphs(parts, stack, rng[:-4]) if parts else b""
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if clean.startswith("/fonts/") and clean.endswith(".pbf") and not os.path.isfile(self.translate_path(clean)):
            # a glyph range this font does not have (rare scripts, symbols): answer with an
            # empty glyph file rather than a 404, so the browser console stays clean
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if clean.endswith(".json"):
            local = self.translate_path(clean)
            if os.path.isfile(local):
                host = self.headers.get("Host", f"localhost:{PORT}")
                with open(local, "rb") as f:
                    body = f.read()
                body = body.replace(b'"/fonts/', f'"http://{host}/fonts/'.encode())
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().do_GET()

    def do_POST(self):
        """POST /clean  (body = the file, header X-Filename = its name)
        -> the cleaned file, with X-Clean-Report = JSON summary of what changed.
        Used by the PNG and Export buttons, so nothing leaves the playground
        with provenance metadata attached."""
        if self.path.split("?", 1)[0] != "/clean":
            self.send_error(404); return
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0 or n > 64 * 1024 * 1024:
            self.send_error(413); return
        data = self.rfile.read(n)
        name = os.path.basename(self.headers.get("X-Filename", "file.bin")) or "file.bin"
        if not os.path.isfile(CLEANER):
            self._send(data, {"error": "cleaner not installed", "changed": False}); return
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, name); dst = os.path.join(d, "clean_" + name)
            with open(src, "wb") as f: f.write(data)
            try:
                r = subprocess.run([sys.executable, CLEANER, "--json", src, "-o", dst],
                                   capture_output=True, text=True, timeout=120)
                try: report = json.loads(r.stdout)
                except ValueError: report = {"error": (r.stderr or r.stdout)[-400:], "changed": False}
                out = open(dst, "rb").read() if os.path.isfile(dst) else data
            except Exception as e:
                report, out = {"error": str(e), "changed": False}, data
        keep = {k: report.get(k) for k in ("kind", "format", "changed", "actions", "bytes_in", "bytes_out",
                                            "still_has_c2pa", "still_has_ai_metadata", "error") if k in report}
        self._send(out, keep)

    def _send(self, body, report):
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Clean-Report", json.dumps(report, ensure_ascii=True))
        self.send_header("Access-Control-Expose-Headers", "X-Clean-Report")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

print(f"Playground at http://localhost:{PORT}  (Ctrl+C to stop)")
print(f"Style URLs for other apps: http://localhost:{PORT}/skins/<name>.json")
print("Export cleaning:", "on (watermarks-remover)" if os.path.isfile(CLEANER) else "off (tools/watermarks-remover missing)")
http.server.ThreadingHTTPServer(("", PORT), Handler).serve_forever()
