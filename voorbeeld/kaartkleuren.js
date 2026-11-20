// Kleuren voor water en groen op de OpenFreeMap-kaart (positron = licht, dark = donker).
// Werkt per bronlaag (source-layer), dus onafhankelijk van de exacte laagnamen.
function kaartKleuren(map, donker) {
  const K = donker
    ? { water: '#1d3f5e', waterlijn: '#2a5478', park: '#1e3b2a', bos: '#1a3a26', gras: '#22402d' }
    : { water: '#a9d3f0', waterlijn: '#8cc3ea', park: '#cfe7bf', bos: '#bcdcab', gras: '#d8edc9' };
  const groen = ['match', ['get', 'class'], ['wood', 'forest'], K.bos, ['grass', 'meadow', 'scrub', 'farmland'], K.gras, K.park];
  for (const l of map.getStyle().layers) {
    const bron = l['source-layer'];
    try {
      if (bron === 'water' && l.type === 'fill') map.setPaintProperty(l.id, 'fill-color', K.water);
      else if (bron === 'waterway' && l.type === 'line') map.setPaintProperty(l.id, 'line-color', K.waterlijn);
      else if (bron === 'park' && l.type === 'fill') { map.setPaintProperty(l.id, 'fill-color', K.park); map.setPaintProperty(l.id, 'fill-opacity', 1); }
      else if (bron === 'landcover' && l.type === 'fill') { map.setPaintProperty(l.id, 'fill-color', groen); map.setPaintProperty(l.id, 'fill-opacity', donker ? 0.9 : 0.85); }
      else if (bron === 'landuse' && l.type === 'fill' && /park|cemetery|grass|pitch|garden|recreation/.test(JSON.stringify(l.filter || ''))) map.setPaintProperty(l.id, 'fill-color', K.park);
    } catch (e) { console.warn(l.id, e.message); }
  }
}
