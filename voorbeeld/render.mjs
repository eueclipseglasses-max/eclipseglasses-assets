import { chromium } from 'playwright';
import fs from 'node:fs';
const kleuren = fs.readFileSync('voorbeeld/kaartkleuren.js', 'utf8');
const html = (stijl, kleur, donker, centrum, zoom) => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>html,body,#map{margin:0;width:100%;height:100%}</style></head><body><div id="map"></div><script>
${kleuren}
const map = new maplibregl.Map({container:'map',style:'https://tiles.openfreemap.org/styles/${stijl}',center:${JSON.stringify(centrum)},zoom:${zoom},attributionControl:false,preserveDrawingBuffer:true});
map.on('style.load',()=>{ if(${kleur}) kaartKleuren(map, ${donker});
  const lagen = map.getStyle().layers.map(l=>l.id+'|'+l.type+'|'+(l['source-layer']||'')); window.LAGEN = lagen; });
map.on('idle',()=>{ window.KLAAR = true; });
</script></body></html>`;
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 420, height: 760 }, deviceScaleFactor: 2 });
fs.mkdirSync('uit', { recursive: true });
const plekken = [['oostende', [2.918, 51.228], 14.2], ['kust', [2.93, 51.225], 12.3]];
for (const [stijl, donker] of [['positron', false], ['dark', true]]) {
  for (const kleur of [false, true]) {
    for (const [naam, c, z] of plekken) {
      await page.setContent(html(stijl, kleur, donker, c, z), { waitUntil: 'load' });
      await page.waitForFunction('window.KLAAR === true', null, { timeout: 90000 });
      await page.waitForTimeout(1500);
      const f = `uit/${stijl}-${kleur ? 'kleur' : 'huidig'}-${naam}.png`;
      await page.screenshot({ path: f });
      console.log('gemaakt', f);
      if (!kleur && naam === 'oostende') fs.writeFileSync(`uit/lagen-${stijl}.txt`, (await page.evaluate('window.LAGEN')).join('\n'));
    }
  }
}
await browser.close();
