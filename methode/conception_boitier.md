# Méthode — concevoir un boîtier à façade (panneau de pupitre, appareil de bureau)

Tirée du F-COM2 (panneau radio, réplique « jour / nuit » de 145,7 × 66,3, 2026-10-26 → 27) et du transpondeur (MFS) ; à suivre
pour chaque nouveau panneau, dans n'importe quel projet. Outils : [`material_library/conception/`](../material_library/conception/summary.md)
(cotes et vérification du dessin, caisson, supports, contrôles 3D, chiffrage) ; arêtes : [`material_library/aretes.py`](../material_library/aretes.py)
et `methode/aretes.md` ; vis : `methode/fixations_facade.md` et `material_library/visserie/`. Essai complet sur un panneau
gabarit : [`essai/`](essai/summary.md).

**Le principe.** On passe les neuf étapes dans l'ordre, et chacune se termine par **une décision de Lou** sur une image ou un
tableau chiffré, pas sur une description. Chaque étape dit **ce qu'on décide**, **comment on le vérifie** (par un outil quand il
existe) et **ce que ça coûte**. On modélise par passes validées une à une : volumes simples → formes secondaires → détails →
matières → asset, avec des **aperçus rapides** à chaque passe et la qualité finale seulement à la fin. Jamais d'arête vive,
même au premier jet.

Repère commun de toutes les maquettes : x à droite (0 = milieu), y en profondeur (0 = face avant de la façade, positif vers
l'arrière), z en haut (0 = bas de la façade), millimètres (1 unité Blender = 1 mm).

---

## 1. Références et normes
**On décide** : quel panneau réel on suit (ou de quelle famille il est), son format, sa disposition, ses inscriptions, sa teinte.

**Comment** :
- Une **fiche de références** (`references.md` du projet) : photos du vrai panneau, fiches de fabricant ou de vendeur, plan coté
  d'une réplique du commerce, modèle 3D à l'échelle 1:1 s'il existe (le meilleur : on y **mesure** au lieu d'estimer sur photo).
  Deux sources qui s'écartent : on en retient une et on note l'écart.
- Chaque cote porte son **statut** : « fiche » (lue ou mesurée sur un modèle 1:1) ou **« estimée »** (photo, déduction) — une cote
  estimée n'est jamais figée comme une norme. `panneau.NORMES` et `panneau.RELEVES` donnent les deux.
- **Normes des pupitres à rails** (toutes « estimées » : déduites des deux panneaux relevés, aucun texte normatif lu) : largeur
  nominale 5,75 in (146,05), hauteurs par **crans de 3/8 in (9,525)**, panneau = cote nominale − 0,015 in (0,38) de jeu, attaches
  d'un même côté à 3 crans (28,58). `panneau.taille(crans)` : 7 crans → 145,67 × 66,29 (radio relevée : 145,7 × 66,3), 6 crans →
  145,67 × 56,77 (transpondeur : 145,7 × 56,8).
- **Inscriptions** : police et hauteur de capitale relevées (ex. 2,85–3,1 sur un panneau réel) ; minimum imprimable en buse 0,4 :
  **2,8** (`REGLES["cap_min_fdm"]`).
- **Teinte** : référence normative (ex. FS 595 36118), équivalents RAL / Pantone classés par écart de couleur, validation sur un
  nuancier physique ; la texture d'un jeu ou d'une photo n'est pas une référence de couleur.

**Règles de Lou** : aucun nom d'avionneur ni de modèle d'avion dans ce qui est public (titres génériques) ; les images de
référence servent à l'étude, elles ne sont jamais publiées.

**Coût** : du temps seulement (½ à 1 journée) ; il évite les refontes : le F-COM2 a changé deux fois de disposition et le
transpondeur une fois de grille avant de suivre les vrais panneaux.

## 2. Taille et architecture
**On décide** : la taille (un vrai format de panneau fait « pièce de cockpit » ; 84 × 36 faisait « jouet »), l'usage (bureau,
pupitre), et l'**empilage en profondeur** :

| y (F-COM2) | Pièce | Rôle |
|---|---|---|
| 0 → 3,0 | plaque de façade (lettres) | ce qui se voit |
| 3,0 → 4,6 | embase | porte les attaches, ferme la lumière, tient cadres et boutons |
| 4,6 → 12,8 | boîte à lumière | chambres des inscriptions, logements des afficheurs, de l'encodeur, des boutons, poches des CMS |
| 12,8 → 14,4 | carte | tout posé sur sa face avant (assemblage une face) |
| 14,4 → 34,6 | caisson (30 de profondeur) | lest, carte USB, inserts du dos, rainures des supports |

`panneau.EMPILAGE` donne ces épaisseurs ; le **dessin à plat** se décrit par un `panneau.Panneau` (ouvertures, inscriptions,
attaches, vis, axes) et se vérifie **avant toute 3D** par `panneau.verifier()` (étape 4).

**Comment on le vérifie** : rendu de face et de trois-quarts à côté de l'objet de référence (même échelle) ; profondeur au plus
juste, prouvée par le contrôle des collisions (étape 7) — le caisson du F-COM2 est passé de 70 à 35 puis 30 mm.

**Coût** : le volume du caisson est le premier poste visible (SLA ≈ 0,18 € TTC le cm³) : chaque 5 mm de profondeur ≈ 1,5 €.

## 3. Matériaux et lieu de fabrication
**On décide**, pièce par pièce : la matière, l'atelier, la finition — **« l'argent là où ça se voit »**.

| Pièce | Se voit ? | Choix du F-COM2 | Pourquoi |
|---|---|---|---|
| Plaque de façade | **oui** | acrylique « jour / nuit » peint, lettres gravées au laser (atelier) | le rétroéclairage réel ; ⚠ prix sur échantillon |
| Embase, boîte à lumière, petites pièces (collerettes, cadres, boutons) | peu / non | PLA chez **l'imprimeur FDM** (buse 0,4) | ≈ 0,6 € de filament contre ≈ 8 € chez JLC pour la boîte à lumière |
| Caisson, supports | **oui** | SLA **JLC Black** poncée et huilée | aspect « injecté » ; le ponçage coûte du temps, pas de l'argent |
| Molette | au toucher | résine 9600 (JLC) | détail fin pour 0,8 € (pas pour cacher la lumière : translucide) |
| Inserts | non | posés à froid **par JLC** | la SLA ne fond pas : pas d'insert à chaud |
| Lest | au poids | masses d'équilibrage adhésives, coupées aux ciseaux | le meilleur rapport « premium » (≈ 0,70 €) |

**Comment** : `chiffrage.sla_jlc(volume)`, `pla_imprimeur(volume)`, `inserts_jlc(n)`, `port_jlc(masse)` sur les volumes mesurés
de la maquette (`controles.volume_cm3`), puis `chiffrage.tableau()` (poste, se voit ?, € par boîtier, choix) ; prix relevés en
2026-10, **à refaire sur devis**. Contraintes connues : buse 0,4 chez l'imprimeur FDM (parois ≥ 1,0, cloisons ≥ 1,2), minimum JLC de
1,05 $ par pièce (grouper les petites pièces en grappe), stock limité chez JLC (réserver les pièces avant une série), Lou ne soude
pas (tout posé par JLC, une seule face en « Economic »).

**Coût** : ce qui fait « premium » pour peu d'argent : le poids, les
vis inox dans leurs collerettes, une molette fine, le caisson poncé huilé, la vitre fumée, une boîte imprimée. Ce qui ne mérite
pas d'argent : tout ce qui est caché.

## 4. Fixations
**On décide** : le **standard du projet** (une seule règle pour toutes les façades) et la place de chaque vis.

- Visserie **du commerce** (DIN / ISO, plusieurs vendeurs) : attaches façade → caisson = **M4 × 8 DIN 84 inox dans une
  collerette** imprimée (trou de la plaque Ø 10,3, ouvert en U s'il reste < 2 mm jusqu'au bord) ; petites vis traversantes = **M3
  ISO 7046 fraisées noires à fleur**, écrou au dos de la carte. Règle complète : `methode/fixations_facade.md`.
- Le caisson prend le contour de la façade (retrait 0,3) et reçoit les attaches dans des **colonnes d'inserts** : rayon borné
  pour rester 0,5 sous la face du flanc et 0,3 des pièces voisines, **≥ 2 mm de matière autour de l'insert**
  (`caisson.rayon_colonne`, qui alerte sinon).
- Places : sur les bords, alignées sur les inscriptions de côté, **≥ 0,8 des lettres**, cloisons ≥ 1,2 avec les ouvertures ;
  les petites vis servent aussi à **serrer la carte** (façade + boîte à lumière + carte d'un seul serrage).

**Comment** : `panneau.verifier(p)` sur le dessin à plat (trou trop près d'une lettre ou d'une ouverture, trou hors du panneau,
attache à ouvrir en U) ; puis en 3D les trous et collisions de l'étape 7.

**Coût** : ≈ 2 € de visserie par boîtier au détail (< 0,50 € en gros) ; inserts JLC ≈ 0,57 € pièce ; collerettes PLA : quelques
centimes. Les vraies vis quart de tour coûtaient 16–20 € par boîtier.

## 5. Lumière
**On décide** : quelles inscriptions sont éclairées (et la couleur : blanc chaud ≈ 2 700 K, ambre…), le procédé de la façade.

- Une **chambre fermée** par inscription dans la boîte à lumière, une LED de la carte au fond (`panneau.chambres(p)`).
- Des **jours dans l'embase** en face de chaque chambre (`panneau.jours_embase()`) : une embase pleine bouche le rétroéclairage.
- Une inscription éclairée doit tomber **au-dessus de la carte** (`Panneau.zone_lumiere`) : sinon pas de LED possible.
- Façade « jour / nuit » : acrylique résistant à la chaleur, blanc diffusant puis gris opaque, lettres gravées au laser à travers
  la peinture ; chants et bords de découpe noircis (3–4 couches), fraisages et trous des attaches faits **avant la peinture**
  (sinon liseré lumineux la nuit autour des vis) ; pas d'aspect verre, peinture mate anti-traces.
- Afficheurs derrière une **vitre fumée foncée (≈ 20–25 %)** : un fumé clair (≈ 45 %) laisse voir les segments éteints.

**Comment** : contrôle de lumière = `controles.trous()` lancé sur le centre de chaque chambre à travers l'embase et la boîte à
lumière (aucune pièce ne doit arrêter le rayon) ; rendu de nuit (studio `nuit`) ; banc d'essai pour la luminosité réelle.

**Coût** : la plaque « jour / nuit » est le prix inconnu du F-COM2 (ateliers sur devis, dès 1 pièce chez certains) :
**échantillon obligatoire**. LED et résistances : centimes, sur la carte.

## 6. Supports et pose
**On décide** : pose à plat (patins) ou inclinée, et l'angle.

- **Supports clipsés** du F-COM1 à l'échelle ×1,6, dessus incliné de **15°**, tenon en queue d'aronde dans une rainure du fond du
  caisson (ouverte au dos, chanfrein de la bouche, entrée évasée), patins 3M dans des poches : `supports.construire()` (supports,
  patins et pose de la racine), `supports.profil_rainure()` et `caisson.construire(…, clipsage=True)` pour la rainure.
- **Patins du caisson livrés à part** (collés par le client seulement pour une pose à plat) : sur les supports ils soulèvent le
  caisson.
- **Lest** caché dans le fond (≈ 400 g visés) : masses adhésives, sans outil.
- Pupitre : caisson au contour de la façade = plus de rebord pour une pose en découpe ; la fixation passe par **4 inserts au dos**
  (`caisson.construire(…, inserts_dos=…)`).

**Comment** : vue « clips » (caisson retourné), contrôle des collisions supports / caisson / patins, pose vérifiée (patins sur
le bureau, rien sous le sol).

**Coût** : 2 supports SLA ≈ 4,5–4,9 € ; lest ≈ 0,70 € ; patins ≈ 0,3 €.

## 7. Contrôles automatiques (à chaque construction de la maquette)
| Contrôle | Outil | Ce qu'il trouve |
|---|---|---|
| Dessin à plat | `panneau.verifier(p)` | trou près d'une lettre / d'une ouverture, cloison < 1,2, lettre éclairée hors de la carte, capitales < 2,8, attache à ouvrir en U |
| Trous bouchés | `controles.trous(axes, pièces)` | rayon le long de chaque vis traversante, axe d'encodeur, chambre de lumière : aucune pièce ne doit l'arrêter |
| Collisions | `controles.collisions(noms, préfixes, voulus)` | pièces qui se pénètrent de plus de 0,06 (surfaces rentrées de 0,03 : un contact ne compte pas) ; contacts voulus par couples de préfixes (insert emmanché, vis dans son insert, pièce multi-matière) |
| Parois minces | `controles.parois(noms, minimum)` | matière plus mince que la buse ou le procédé le permet (1,2 cloison FDM, 0,8 fond de collerette, 1,0 SLA) |
| Colonnes | `caisson.rayon_colonne()` | matière autour d'un insert < 2 mm, colonne qui ressortirait du flanc |
| Arêtes vives | `aretes.aretes_vives(objet)` | arêtes de plus de 45° (règle : `methode/aretes.md`) |
| Volumes | `controles.volume_cm3(nom)` | les volumes du chiffrage |

Le bilan s'affiche en une ligne par contrôle (`CONTROLE … : 0 …`) ; une maquette ne part en rendu ou en devis qu'à **0 erreur**.
Les noms d'objets portent un **préfixe par produit** (`GF_` au F-COM2, `GAB_` pour l'essai) : les contrôles prennent des préfixes.

**Coût** : quelques secondes par construction ; chaque défaut trouvé ici aurait coûté une impression ratée.

## 8. Chaîne de rendu
1. La maquette construit **l'asset** (un `.blend` par produit : shading enregistré dedans, racine et commandes `pose`, `eclate`,
   `a_plat`, `clips`, `allume`…), avec archive de l'ancien et refus d'écraser sans `force` (Lou retouche parfois le shading) ;
   chaque vue rejouée par les commandes est vérifiée identique à la vue construite.
2. Les **plans fixes** (un `.blend` par vue) **lient** l'asset et le studio, jamais une copie.
3. **Aperçus** rapides (peu d'échantillons, studio réel) à chaque passe de modélisation, montrés à Lou ; couleurs contrôlées à la
   pipette sur le rendu (le studio du site rend les gris ≈ 2 fois trop clairs : bases compensées).
4. **Rendus finaux** HD seulement après validation, sur la ferme (skill `rendu-distant`, PC-B), puis copiés dans le dépôt du projet.
5. Toute modification de la bibliothèque utilisée par un projet : **non-régression** (`outils/non_regression.py` : dumps avant /
   après) et un aperçu à l'œil.

**Coût** : un aperçu ≈ 1–3 min sur ce PC ; un rendu HD ≈ 10–30 min par vue sur PC-B.

## 9. Revue de faisabilité et chiffrage
**On décide** : on commande ou on corrige.

- **Montage écrit pas à pas** (ordre des pièces, outillage, temps) : il fait apparaître ce qui ne se monte pas (vitre qui ne
  tient qu'avec la boîte à lumière, câble à brancher avant de fermer…).
- **Usage** : course des boutons (jour 0,2 + course + marge 0,15 : recul de 0,6 pour un TS-1187A), jour derrière une molette
  (≥ 1,2 pour un poussoir de 0,5), démontage.
- **Liste « à vérifier sur le premier boîtier »** (ce que la maquette ne peut pas trancher : ajustements serrés, planéité d'une
  grande pièce SLA, luminosité, reflets) ; **lot d'essai** (un plateau de 3 boîtiers chez l'imprimeur FDM) avant la série.
- **Tableau chiffré** (`chiffrage.tableau`) avec la cible ; devis avant commande ; **c'est Lou qui commande**.

**Coût** : ½ journée ; le lot d'essai ≈ 6 h de machine et un colis.

---

## Pièges vécus sur le F-COM2 (et le transpondeur)
Chaque ligne a coûté au moins un aller-retour avec Lou ; la parade est dans les outils ou la règle citée.

| # | Piège | Ce qui s'est passé | Parade |
|---|---|---|---|
| 1 | Taille « jouet » | 84 × 36 « fait jouet pour enfant » | un vrai format de panneau (étape 1, `panneau.taille`) |
| 2 | Caisson trop profond | 70 → 35 → 30 mm, pour le coût | profondeur minimale prouvée par les collisions |
| 3 | Cales massives | boîtier trop surélevé, « pas harmonieux » | supports clipsés du F-COM1 ×1,6 (`supports.construire`) |
| 4 | Vis quart de tour | vraies : 16–20 € par boîtier ; imitations : à fabriquer ; godets, manchons, rondelle, vis cruciformes noires puis fendues : 6 allers-retours | **visserie du commerce** + collerette (`fixations_facade.md`), décidée une fois pour toutes les façades |
| 5 | Style des coins | coins en L autour des vis, puis réplique à petits rayons | choisir le panneau de référence (étape 1) avant de dessiner les coins |
| 6 | Colonnes qui ressortaient | colonnes d'insert R 6 hors du flanc après le recentrage des vis | rayon borné (`caisson.rayon_colonne`, ≥ 2 mm autour de l'insert) |
| 7 | Insert à chaud dans la SLA | la résine ne fond pas | inserts posés par JLC (0,57 €) |
| 8 | Jours oubliés | embase pleine : rétroéclairage bouché | `panneau.jours_embase` + contrôle de lumière |
| 9 | Inscriptions hors de la carte | VHF / COMM sur les côtés, hors du caisson : pas de LED possible | `Panneau.zone_lumiere` dans `verifier` |
| 10 | Boutons qui ne s'enclenchaient pas | 0,3 de recul pour 0,45 nécessaire | recul 0,6 (jour + course + marge), étape 9 |
| 11 | Molette qui frotte | 0,5 de jour pour 0,5 de course | 1,2 de jour |
| 12 | Vitre tenue par une autre pièce | montage impossible sans vitre | nervures d'écrasement dans le cadre : chaque pièce tient seule |
| 13 | Cloison de 0,5 | non imprimable en buse 0,4 | logements réunis ; `controles.parois(…, 1.2)` |
| 14 | Patins sur les supports | caisson soulevé, clipsage impossible | patins livrés à part |
| 15 | Vis du bas dans la paroi | vis à z 4,5 dans la paroi du fond, pointes contre l'appui du lest | vis remontées à z 9, appui dégagé ; `controles.trous` / `collisions` |
| 16 | Arêtes vives au clipsage | arêtes qui s'écaillent, tenon qui accroche | chanfrein 0,5 à la bouche, entrée évasée 0,6 (`supports.profil_rainure`) |
| 17 | « Angles droits trop sharps » | acrylique à arêtes vives au rendu | nœud Bevel R 0,4 + congés des découpes (`aretes`) |
| 18 | Maillages ouverts | arêtes ouvertes au tenon (STL refusé), arêtes non manifold autour des lettres incrustées | maillage refermé ; à contrôler avant l'export STL |
| 19 | Liseré lumineux | fraisages faits après la peinture « jour / nuit » | fraiser et percer avant peinture (`fixations_facade.md`) |
| 20 | Segments éteints visibles | vitre fumée claire (≈ 45 %) | fumé foncé ≈ 20–25 % |
| 21 | Gris trop clairs au rendu | le studio rend ≈ 2 fois plus clair | base compensée à la pipette, contrôle sur le rendu |
| 22 | Lettres « trop nettes, trop blanches » | blanc pur, contour parfait | simulation d'impression (buse 0,2), jamais de blanc absolu |
| 23 | Cotes lues sur une copie qui bouge | le fichier d'une autre session changeait pendant la lecture | lire la version **commitée** |
| 24 | Rendus vides ou faux | caméra sous le bureau, coupe à 100 mm par défaut dans une scène en mm, supports sous le sol dans l'éclaté | `clip_start` réglé, alerte caméra sous le bureau, pose vérifiée |
| 25 | Norme mal lue | tête M2,5 ISO 7045 = Ø 5,0, pas 4,5 (transpondeur) | lire la table (`visserie/normes.py`), pas la mémoire |
| 26 | Stock JLC | 262 afficheurs = 65 boîtiers | réserver les pièces avant une série, plan B au même brochage |
| 27 | Pose en pupitre | caisson élargi au contour de la façade : plus de rebord pour un panneau découpé | inserts au dos |

Pièges des outils, trouvés en écrivant cette méthode (2026-10-27) : un booléen laisse des faces concaves que `BVHTree.FromPolygons`
triangule en éventail (fausses collisions : `controles` utilise les triangles de Blender) ; `bound_box` d'un objet dont on vient
de transformer le maillage est périmé (mesurer sur les sommets).

## Essai : un panneau gabarit
[`essai/essai_panneau_gabarit.py`](essai/essai_panneau_gabarit.py) passe un panneau simple de 5 crans (fenêtre d'afficheur,
bouton, deux inscriptions éclairées, quatre attaches, deux petites vis) par les étapes 1 à 9 avec les seuls outils ci-dessus,
sans code du F-COM2. Résultats et aperçus : [`essai/summary.md`](essai/summary.md).
