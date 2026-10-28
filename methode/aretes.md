# Arêtes — aucune arête vive

Règle de Lou (2026-09-29) : « on ne veut jamais d'angle 90° parfait bien sharp ». Toute pièce dessinée (boîtier, supports,
visserie, packaging…) a des arêtes chanfreinées ou arrondies, y compris les découpes faites après coup (rainures, perçages, poches,
tenons). Raisons : rendu pro, toucher, robustesse (une arête vive amorce les fissures).
Outils : [`material_library/aretes.py`](../material_library/aretes.py) ; planche de contrôle :
[`outils/planches/planche_aretes.py`](../outils/planches/planche_aretes.py) ; essai : `outils/essais/essai_aretes.py`.

## Géométrie ou rendu ?
| Situation | Moyen | Fonction |
|---|---|---|
| L'arête se voit **en silhouette** (contour d'une plaque, bord d'une fenêtre vu de biais) ou **se fabrique** (rayon de fraise, congé d'impression, chanfrein laser) | biseau ou congé **dans le maillage** (il part dans les STL) | `plaque(…, arr=(av, ar))`, `coupe(…, conge=r)` ou `coupe(…, chanf=c)`, `adoucir(ob, largeur)` |
| Toutes les autres arêtes, pour qu'aucune ne « coupe » la lumière à l'image | **nœud Bevel** de Cycles sous le relief de la matière (volume et STL inchangés) | `bevel_rendu(matiere, r)`, `aretes_douces(matieres, sauf=…)` |

Les deux se cumulent : une pièce a ses congés fabriqués **et** sa matière a son nœud Bevel (il arrondit ce qui reste vif : dos
des découpes, petites arêtes de booléen).

Le nœud Bevel ne marche **qu'en Cycles** (EEVEE l'ignore) ; il ne change ni le volume, ni les STL, ni la silhouette.

## Rayons par défaut (nœud Bevel, mm) — `aretes.RAYONS`
| Matière | r | D'où ça vient |
|---|---|---|
| acrylique peint (plaque « jour / nuit ») | 0,4 | Lou, 2026-10-27 : « la face acrylique a toujours des angles droits trop sharps » |
| PLA FDM (imprimeur FDM) | 0,3 | pièces imprimées du F-COM2 |
| résine SLA (JLC), nylon MJF | 0,25 | `aretes_douces` du F-COM1 |
| molette | 0,6 | Lou, 2026-10-25 : bords trop vifs à 0,25 |
| têtes de vis | 0,2 | frappe à froid (photos de vis oxydées) |
| cartes électroniques | 0,15 | `pcb_photoreal` |

Une matière peut porter sa propre valeur (propriété `arrondi`), prioritaire sur le défaut. Les congés géométriques reprennent
les mêmes ordres de grandeur (0,4 à 0,6 sur les découpes visibles d'une façade).

## Lissage et topologie
- Lissage **par angle** (35°, `ANGLE_LISSE`) : au-delà, l'arête reste marquée ; en deçà (congés à 15° par segment), tout est lisse.
- Après un **booléen** : `retrancher()` lisse par angle **puis pondère les normales** par l'aire des faces ; sans cela, les longs
  triangles laissés par le booléen tirent l'ombrage de la face plane (traînées, lignes sombres le long d'un congé — vu le
  2026-10-27). Pour un dessus de vis, préférer **une seule face plane** à un éventail de triangles (traînées en étoile).
- Maillage généré à la main (bmesh) : topologie régulière **et** arêtes de contention (boucles de maintien) à ~0,05 mm d'une
  arête non adoucie, à (largeur du biseau + 0,05) d'une arête adoucie par modificateur ; sinon le lissage tire les faces planes.
- Une pièce fabriquée d'un bloc = **un seul maillage** (une tôle pliée avec ses plis, pas des morceaux juxtaposés).

## Découpes à congé (`coupe`)
- Le congé est un quart de cercle tangent à la face visible (`y_face`) et à la paroi ; 6 segments suffisent (12 donnent la
  même image : la bande claire / sombre le long d'un congé de 0,6 est le **reflet du studio**, pas un facettage).
- Seule la face visible est arrondie : le dos de la découpe reste vif (non vu ; le nœud Bevel l'adoucit au rendu).
- **Encoche ouverte sur un bord** (`encoche_u`) : son entrée est arrondie (rayon `rf`) ; un congé ou un chanfrein ≥ `rf` ferait
  croiser le contour (bug du 2026-10-27) → refusé (`ValueError`). Garder `rf` ≥ congé + 0,05.
- À la jonction de deux congés (entrée d'une encoche dans le contour arrondi de la plaque), il reste quelques arêtes de 46 à
  65° sur moins de 0,1 mm : invisibles, adoucies par le nœud Bevel.

## Exceptions (arêtes vives admises)
- Frontières **internes** entre matières d'une pièce multi-matière (lettres à fleur dans la façade, flèche du bouton TFR) : elles
  ne se voient pas une fois imprimées ; et le nœud Bevel y dessinerait un liseré sombre → ces matières vont dans `sauf=`.
- Surfaces planes d'affichage (écran, étiquette) : pas de Bevel.

## Vérifier
- **Par mesure**, pas seulement à l'œil : `aretes_vives(ob, 45)` liste les arêtes du maillage évalué de plus de 45° (le dos des
  découpes et les exceptions ci-dessus mis à part, la liste doit être vide).
- **À l'image** : gros plan de face et en lumière rasante dans le studio du site ; la planche d'arêtes (rayons 0 / 0,2 / 0,4 /
  0,6, géométrie et rendu) sert de référence.
