// Render a small thumbnail of every non-country skin into playground/thumbs/<id>.png
const puppeteer = require('puppeteer-core');
const fs = require('fs'), path = require('path');
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const OUT = 'C:/Users/sabri/Desktop/My Map/playground/thumbs';
fs.mkdirSync(OUT, { recursive: true });
const skins = JSON.parse(fs.readFileSync('C:/Users/sabri/Desktop/My Map/playground/skins.json', 'utf8'))
  .filter(s => s.group !== 'Countries');

(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: true,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
    defaultViewport: { width: 360, height: 240, deviceScaleFactor: 1 } });
  const page = await browser.newPage();
  for (const s of skins) {
    const file = path.join(OUT, s.id + '.png');
    if (fs.existsSync(file) && !process.env.FORCE) { console.log('skip', s.id); continue; }
    const meta = (() => { try { return JSON.parse(fs.readFileSync('C:/Users/sabri/Desktop/My Map/playground/' + s.file, 'utf8')).metadata.playground || {}; } catch (e) { return {}; } })();
    const view = meta.center ? `#${meta.zoom || 15}/${meta.center[1]}/${meta.center[0]}` : (s.id === 'earth' ? '#2/25/-7' : '#15.5/33.5935/-7.618');
    try {
      await page.goto(`http://localhost:3030/?skin=${s.id}${view}`, { waitUntil: 'load' });
      await page.addStyleTag({ content: '#hud,#pos,.maplibregl-ctrl{display:none!important}' });
      await page.waitForFunction(() => typeof map !== 'undefined' && map.loaded() && map.areTilesLoaded() && !map.isMoving(), { timeout: 60000, polling: 250 });
      await page.evaluate(() => new Promise(r => { map.once('idle', r); setTimeout(r, 4000); }));
      await new Promise(r => setTimeout(r, 1500));
      await page.screenshot({ path: file });
      console.log('ok', s.id);
    } catch (e) { console.log('FAIL', s.id, e.message.slice(0, 80)); }
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
