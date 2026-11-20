// Kleuren voor water en groen op de OpenFreeMap-kaart (positron = licht, dark = donker).
// Werkt per bronlaag (source-layer), dus onafhankelijk van de exacte laagnamen.
// Parken, grasvelden en bos zitten in de bronlaag 'landcover', die positron/dark niet tekenen: we voegen een laag toe.
function kaartKleuren(map, donker) {
  const K = donker
    ? { water: '#1d3f5e', waterlijn: '#2a5478', park: '#21452f', gras: '#1d3a28', bos: '#1b3a26', sport: '#22412d' }
    : { water: '#a9d3f0', waterlijn: '#8cc3ea', park: '#c4e3b2', gras: '#d6ebc6', bos: '#b9dba6', sport: '#cfe7bf' };
  const stijl = map.getStyle();
  const bron = (stijl.layers.find(l => l['source-layer'] === 'landcover' || l['source-layer'] === 'water') || {}).source;
  const voorWater = (stijl.layers.find(l => l['source-layer'] === 'water') || {}).id;
  for (const l of stijl.layers) {
    const sl = l['source-layer'];
    try {
      if (sl === 'water' && l.type === 'fill') map.setPaintProperty(l.id, 'fill-color', K.water);
      else if (sl === 'waterway' && l.type === 'line') map.setPaintProperty(l.id, 'line-color', K.waterlijn);
      else if (sl === 'landcover' && l.type === 'fill' && /wood/.test(l.id)) { map.setPaintProperty(l.id, 'fill-color', K.bos); map.setPaintProperty(l.id, 'fill-opacity', 0.9); }
      else if (sl === 'park' && l.type === 'fill') { map.setPaintProperty(l.id, 'fill-color', K.park); map.setPaintProperty(l.id, 'fill-opacity', 0.6); }
    } catch (e) { console.warn(l.id, e.message); }
  }
  if (bron && !map.getLayer('golem-groen')) {
    map.addLayer({ id: 'golem-groen', type: 'fill', source: bron, 'source-layer': 'landcover',
      filter: ['match', ['get', 'class'], ['grass', 'wood', 'forest'], true, false],
      paint: { 'fill-color': ['match', ['get', 'subclass'], ['park', 'garden', 'recreation_ground', 'village_green', 'playground'], K.park, ['wood', 'forest'], K.bos, K.gras], 'fill-opacity': 0.9 } }, voorWater);
    map.addLayer({ id: 'golem-groen-terrein', type: 'fill', source: bron, 'source-layer': 'landuse',
      filter: ['match', ['get', 'class'], ['cemetery', 'pitch', 'stadium', 'playground', 'park'], true, false],
      paint: { 'fill-color': K.sport, 'fill-opacity': 0.8 } }, voorWater);
  }
}
