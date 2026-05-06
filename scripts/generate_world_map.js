/**
 * generate_world_map.js
 * ---------------------
 * Converts the world-atlas TopoJSON (Natural Earth 110m, public domain)
 * into a compact SVG where every country <path> has id="XX" matching its
 * ISO 3166-1 alpha-2 code.
 *
 * Usage: node scripts/generate_world_map.js
 * Output: src/assets/world-map.svg
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { feature } from 'topojson-client'

// Also outputs: src/data/country-bboxes.json
// Format: { "US": [minLon, minLat, maxLon, maxLat], ... }
// Countries that straddle the antimeridian get null (handled gracefully in frontend)

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')

// ---------------------------------------------------------------------------
// ISO 3166-1 numeric -> alpha-2 mapping
// (Natural Earth uses numeric codes in world-atlas)
// ---------------------------------------------------------------------------
const NUM_TO_A2 = {
  4:'AF',8:'AL',12:'DZ',20:'AD',24:'AO',32:'AR',36:'AU',40:'AT',31:'AZ',
  44:'BS',48:'BH',50:'BD',52:'BB',112:'BY',56:'BE',84:'BZ',204:'BJ',
  64:'BT',68:'BO',70:'BA',72:'BW',76:'BR',96:'BN',100:'BG',854:'BF',
  108:'BI',132:'CV',116:'KH',120:'CM',124:'CA',140:'CF',148:'TD',152:'CL',
  156:'CN',170:'CO',174:'KM',178:'CG',180:'CD',188:'CR',191:'HR',192:'CU',
  196:'CY',203:'CZ',208:'DK',262:'DJ',212:'DM',214:'DO',218:'EC',818:'EG',
  222:'SV',226:'GQ',232:'ER',233:'EE',748:'SZ',231:'ET',242:'FJ',246:'FI',
  250:'FR',266:'GA',270:'GM',268:'GE',276:'DE',288:'GH',300:'GR',308:'GD',
  320:'GT',324:'GN',624:'GW',328:'GY',332:'HT',340:'HN',348:'HU',352:'IS',
  356:'IN',360:'ID',364:'IR',368:'IQ',372:'IE',376:'IL',380:'IT',388:'JM',
  392:'JP',400:'JO',398:'KZ',404:'KE',296:'KI',414:'KW',417:'KG',418:'LA',
  428:'LV',422:'LB',426:'LS',430:'LR',434:'LY',438:'LI',440:'LT',442:'LU',
  450:'MG',454:'MW',458:'MY',462:'MV',466:'ML',470:'MT',584:'MH',478:'MR',
  480:'MU',484:'MX',583:'FM',498:'MD',492:'MC',496:'MN',499:'ME',504:'MA',
  508:'MZ',104:'MM',516:'NA',520:'NR',524:'NP',528:'NL',554:'NZ',558:'NI',
  562:'NE',566:'NG',408:'KP',807:'MK',578:'NO',512:'OM',586:'PK',585:'PW',
  275:'PS',591:'PA',598:'PG',600:'PY',604:'PE',608:'PH',616:'PL',620:'PT',
  634:'QA',642:'RO',643:'RU',646:'RW',659:'KN',662:'LC',670:'VC',882:'WS',
  674:'SM',678:'ST',682:'SA',686:'SN',688:'RS',690:'SC',694:'SL',702:'SG',
  703:'SK',705:'SI', 90:'SB',706:'SO',710:'ZA',410:'KR',728:'SS',724:'ES',
  144:'LK',729:'SD',740:'SR',752:'SE',756:'CH',760:'SY',158:'TW',762:'TJ',
  834:'TZ',764:'TH',626:'TL',768:'TG',776:'TO',780:'TT',788:'TN',792:'TR',
  795:'TM',798:'TV',800:'UG',804:'UA',784:'AE',826:'GB',840:'US',858:'UY',
  860:'UZ',548:'VU',336:'VA',862:'VE',704:'VN',887:'YE',894:'ZM',716:'ZW',
  // Territories / special codes that appear in Natural Earth
  10:'AQ',   // Antarctica
  304:'GL',  // Greenland (part of Denmark in NE data, id 304)
  630:'PR',  // Puerto Rico
  234:'FO',  // Faroe Islands
  238:'FK',  // Falkland Islands
  540:'NC',  // New Caledonia
  258:'PF',  // French Polynesia
  60:'BM',   // Bermuda
  316:'GU',  // Guam
  850:'VI',  // US Virgin Islands
  531:'CW',  // Curaçao
  534:'SX',  // Sint Maarten
  533:'AW',  // Aruba
  175:'YT',  // Mayotte
  638:'RE',  // Réunion
  654:'SH',  // Saint Helena
  744:'SJ',  // Svalbard
  580:'MP',  // N. Mariana Islands
  581:'UM',  // US Minor Outlying Islands
  772:'TK',  // Tokelau
  876:'WF',  // Wallis and Futuna
  // Kosovo (used by Natural Earth as 383)
  383:'XK',
  // Taiwan (used as 158 above, but NE sometimes uses -99 for disputed)
}

// ---------------------------------------------------------------------------
// Equirectangular projection
// ---------------------------------------------------------------------------
const W = 1010
const H = 506

function project([lon, lat]) {
  return [
    ((lon + 180) * W) / 360,
    ((90 - lat) * H) / 180,
  ]
}

function ringToD(ring) {
  return ring
    .map(([lon, lat], i) => {
      const [x, y] = project([lon, lat])
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join('') + 'Z'
}

function geometryToD(geometry) {
  const { type, coordinates } = geometry
  if (type === 'Polygon') {
    return coordinates.map(ringToD).join('')
  }
  if (type === 'MultiPolygon') {
    return coordinates.flatMap(poly => poly.map(ringToD)).join('')
  }
  return ''
}

/** Collect all lon/lat coordinate pairs from a geometry. */
function collectCoords(geometry) {
  const { type, coordinates } = geometry
  const rings = type === 'Polygon'
    ? coordinates
    : type === 'MultiPolygon'
      ? coordinates.flatMap(p => p)
      : []
  return rings.flatMap(ring => ring)
}

/** Return [minLon, minLat, maxLon, maxLat] or null for antimeridian-straddling features. */
function geoBbox(geometry) {
  const coords = collectCoords(geometry)
  if (!coords.length) return null
  let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity
  for (const [lon, lat] of coords) {
    if (lon < minLon) minLon = lon
    if (lon > maxLon) maxLon = lon
    if (lat < minLat) minLat = lat
    if (lat > maxLat) maxLat = lat
  }
  // Countries whose longitude span > 180° likely straddle the antimeridian.
  // Mark as null — the frontend will show the full map for these.
  if (maxLon - minLon > 180) return null
  return [
    parseFloat(minLon.toFixed(2)),
    parseFloat(minLat.toFixed(2)),
    parseFloat(maxLon.toFixed(2)),
    parseFloat(maxLat.toFixed(2)),
  ]
}

// ---------------------------------------------------------------------------
// Load world-atlas and generate SVG
// ---------------------------------------------------------------------------
const topoPath = join(ROOT, 'node_modules', 'world-atlas', 'countries-110m.json')
const topo = JSON.parse(readFileSync(topoPath, 'utf8'))
const { features } = feature(topo, topo.objects.countries)

const paths = []
const bboxes = {}   // iso2 -> [minLon, minLat, maxLon, maxLat] | null
let skipped = 0

for (const f of features) {
  const numId = parseInt(f.id, 10)
  const iso2 = NUM_TO_A2[numId]
  if (!iso2) {
    skipped++
    continue
  }
  const d = geometryToD(f.geometry)
  if (!d) { skipped++; continue }
  paths.push(`  <path id="${iso2}" d="${d}"/>`)
  bboxes[iso2] = geoBbox(f.geometry)
}

const svg = `<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 ${W} ${H}"
     data-source="Natural Earth 110m (public domain), equirectangular projection">
  <style>
    path {
      fill: #d1d5db;
      stroke: #ffffff;
      stroke-width: 0.5;
      stroke-linejoin: round;
      vector-effect: non-scaling-stroke;
    }
    path.highlighted {
      fill: #6b9e78;
    }
  </style>
${paths.join('\n')}
</svg>`

const outPath = join(ROOT, 'src', 'assets', 'world-map.svg')
mkdirSync(dirname(outPath), { recursive: true })
writeFileSync(outPath, svg, 'utf8')

// Also write the bounding-box lookup used by the frontend zoom logic
const bboxPath = join(ROOT, 'src', 'data', 'country-bboxes.json')
writeFileSync(bboxPath, JSON.stringify(bboxes, null, 2), 'utf8')

const kb = Math.round(svg.length / 1024)
const nullCount = Object.values(bboxes).filter(v => v === null).length
console.log(`Generated ${paths.length} country paths, skipped ${skipped}`)
console.log(`Bboxes: ${Object.keys(bboxes).length} countries, ${nullCount} antimeridian-straddling (stored as null)`)
console.log(`SVG written to:   ${outPath}  (${kb} KB)`)
console.log(`Bboxes written to: ${bboxPath}`)
