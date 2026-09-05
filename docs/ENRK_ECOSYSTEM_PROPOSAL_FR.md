# ENRK — Un stablecoin adossé à l'énergie sur les covenants Kaspa L1

**Proposition à la Kaspa Ecosystem Foundation et aux développeurs cœur de Kaspa**

*Version française. English version: `ENRK_ECOSYSTEM_PROPOSAL.md`*

**Date :** septembre 2026
**Dépôt :** https://github.com/cyprox/ENRK_stablecoin
**État :** conception et spécification terminées. Avant implémentation. Nous
cherchons une validation technique et un partenariat d'audit.

---

## Résumé

ENRK est un stablecoin surcollatéralisé dont l'unité de compte est **un
kilowattheure de valeur thermodynamique**, et non une monnaie fiduciaire. Il est
conçu pour être **immuable après déploiement** : pas de DAO, pas de clé
d'administration, aucun chemin de mise à jour. L'évolution se fait par fork, choisi
par les utilisateurs.

Nous pensons qu'il peut être construit **nativement sur Kaspa L1**, avec les
primitives de covenants livrées par Toccata en juin 2026, **sans pont et sans
dépositaire**.

Ce document expose la construction, les preuves qui la soutiennent, ce que nous
avons trouvé de défectueux dans notre propre conception, et ce que nous demandons.

Nous ne demandons pas d'argent en premier. Nous posons d'abord une question
technique (§7.1). Si la réponse est non, cette proposition est caduque et nous
préférons le savoir maintenant.

---

## 1. Ce qu'est le protocole

| | |
|---|---|
| **Unité de compte** | 1 ENRK = 1 kWh de valeur thermodynamique. Pas de dollar, pas de fiat. |
| **Indice de peg** | 40 % hashrate Kaspa, 30 % prix mondial de l'énergie, 20 % frais Kaspa, 10 % adoption crypto. Pondérations gelées. |
| **Collatéral** | KAS, surcollatéralisé. |
| **Structure** | Double tranche — ENRK (senior, rachetable) et kFIAT (junior, absorbeur de pertes, plafonné à 30 % de la dette à l'émission). |
| **Liquidation** | Enchère hollandaise, sans permission. |
| **Gouvernance** | **Aucune.** Tous les paramètres gelés à la compilation. |

La thèse thermodynamique est ce qui fait de Kaspa la bonne chaîne plutôt qu'une
chaîne arbitraire : le KAS a un coût de production ancré dans la consommation
électrique de la preuve de travail. Si le prix passe sous ce coût, les mineurs
s'éteignent, le hashrate chute, la difficulté s'ajuste, et le coût se réaligne sur
le prix. Le collatéral et l'unité de compte sont liés **causalement** par le
mécanisme de consensus lui-même. Ce lien n'existe pas sur une chaîne en preuve
d'enjeu, et c'est pourquoi cette conception a sa place ici.

---

## 2. Pourquoi Kaspa L1, et l'alternative que nous avons écartée

Nous avons évalué sérieusement Igra EVM et étions prêts à y déployer. Solidity, la
lignée éprouvée de Liquity, un large marché d'audit, une résistance au MEV héritée
de l'ordonnancement par la couche de base. Sur le plan de l'ingénierie, c'est la
voie la plus sûre.

Nous l'avons écartée pour deux raisons que nous n'avons pas su franchir.

**Le collatéral serait chez un dépositaire.** Les deux ponts KAS documentés sont
contrôlés par des opérateurs. La voie officielle est un multisig manuel, 48 à 72
heures de délai, sans garantie de service. KAT Bridge est nettement meilleur sur le
plan opérationnel — 2 à 5 minutes, contrats publiés, quatre audits, réconciliation
publique et continue des réserves — mais c'est un seuil 3-sur-5 dont les cinq
signataires sont exploités par une seule organisation et ne sont pas nommés
publiquement, sans caution ni pénalité. Sa propre documentation indique clairement
que trois signataires coalisés pourraient vider le coffre.

**Les deux routes KAS sont plafonnées à ~200 000 KAS par 24 heures.** Pour un
protocole détenant de l'ordre de 100 M de KAS de collatéral, cela représente
environ 500 jours pour déboucler. Le débit de sortie fixe un plafond dur à la
taille de tout stablecoin qui vit derrière.

Un protocole immuable posé sur un pont dépositaire est immuable dans la partie qui
compte le moins. Sur Kaspa L1, le collatéral ne bouge jamais, et le seul composant
de confiance est un oracle de prix — qui peut mal évaluer des liquidations, mais ne
peut rien emporter.

Ce n'est pas une différence de degré. C'est une catégorie de risque différente, et
c'est toute la raison de cette proposition.

---

## 3. Le cœur technique : un oracle de prix sans contention, par covenants

C'est la partie que nous souhaitons le plus voir relue, car tout le reste en dépend.

### 3.1 Le problème

Un protocole CDP a besoin d'un prix lisible par de nombreuses transactions
concurrentes. Kaspa L1 n'a pas de *reference inputs* — KIP-10 indique directement
qu'aucun opcode ne permet de lire un UTXO non dépensé — et pas d'oracle intégré.
Nous avions d'abord conclu que la voie L1 était fermée.

Cette conclusion était fausse. **Le protocole n'a pas besoin de lire sans
dépenser.** Il peut dépenser un UTXO d'oracle publié précisément pour cela, dans la
même transaction que l'opération qui a besoin du prix.

### 3.2 La construction

Uniquement avec des opcodes livrés :

```
KIP-10 :   OpTxInputAmount (0xbe)   montant de l'entrée N
           OpTxInputSpk    (0xbf)   script pubkey de l'entrée N

KIP-20 :   OpInputCovenantId        covenant_id 32 octets de l'entrée N
           OpAuthOutputCount        sorties autorisées d'une entrée covenant
           OpAuthOutputIdx          index de la k-ième sortie autorisée
```

**Mise en place.** L'oracle crée un UTXO covenant genèse. Son `covenant_id` est gelé
dans chaque script de coffre.

**À chaque tour de prix.** L'oracle le dépense en split un-vers-plusieurs, produisant
N UTXO enfants, tous porteurs du même `covenant_id`, chacun encodant le prix courant
dans son montant. KIP-20 le prévoit explicitement : *« A common pattern is a single
covenant input authorizing one or many covenant outputs in the spending
transaction. »*

**Consommation.** Un liquidateur construit une transaction avec le coffre en entrée 0
et un UTXO d'oracle en entrée 1. Le covenant du coffre vérifie :

```
OpInputCovenantId(1) == ORACLE_COVENANT_ID     authenticité, par lignée
prix := OpTxInputAmount(1)                      la valeur
```

L'authenticité vient de la lignée du covenant et non d'une vérification de
signature — ce qui importe, car le script Kaspa ne dispose d'aucun opcode pour
vérifier une signature sur un message arbitraire. Les identifiants de covenant
contournent entièrement cette limitation.

**L'UTXO d'oracle a deux branches :**

```
USAGE (n'importe qui)   dépensable si (a) la transaction dépense aussi un UTXO
                        de la lignée VAULT, et (b) une sortie est créée portant
                        le même covenant_id et le même montant

BALAYAGE (oracle)       OP_CHECKSIG contre la clé de l'oracle ; permet la
                        republication à un nouveau prix
```

### 3.3 Pourquoi les trois exigences se résolvent

| | |
|---|---|
| **Pas de contention** | N UTXO vivants simultanément ; chaque consommateur en prend un différent. |
| **Résistance au DoS** | La branche usage impose une réplication à l'identique — qui consomme doit recréer, donc le flux ne peut pas être drainé. La condition (a) oblige en plus l'attaquant à toucher un vrai coffre. |
| **Fraîcheur** | Balayage et republication ont lieu dans **une seule transaction**. Le tour R est consommé et le tour R+1 créé atomiquement. Il n'existe aucun instant où les deux coexistent, donc aucune fenêtre de prix périmé. |

Un prix périmé est un vecteur de vol, pas une gêne — un liquidateur qui peut choisir
un vieux prix favorable liquide des coffres sains au vrai prix. La transition
atomique supprime entièrement la fenêtre.

### 3.4 Pourquoi la transition atomique est gratuite — KIP-9

L'objection évidente est le coût. Sous les règles de masse de stockage de Kaspa, il
n'y en a pas. KIP-9 énonce : *« Compounding several outputs into an equal or smaller
number of outputs of equal value will never incur storage mass. This is true
regardless of the magnitude. »*

Pour N entrées de valeur `a` et N sorties de valeur `b`, la formule
`C·(Σ(1/o) − |I|²/Σ(v))⁺` se réduit à `C·N·(1/b − 1/a)⁺`, d'où une asymétrie qui
façonne la conception :

- **un prix qui monte est gratuit** — le terme devient négatif et s'écrête à zéro
- **un prix qui baisse coûte de la masse**, proportionnellement à N et à l'ampleur
  de la baisse

La contrainte est `N·(1/k − 1) ≤ limite` pour un rapport de prix `k` par tour. Borner
étroitement le mouvement par tour permet un N élevé, ce qui pousse vers des **tours
fréquents de faible amplitude** — ce qu'un bon oracle doit faire de toute façon.

---

## 4. Preuves : ce que nous avons trouvé de faux chez nous

Nous avons construit un stress test Monte-Carlo du protocole entier — pas seulement
de la formule de peg — avec population de coffres, liquidation à pénurie réaliste
d'acheteurs, cascade de séniorité, impact réflexif du collatéral vendu, risque de
saut, et contrainte de capital des liquidateurs. Il est dans le dépôt et tourne avec
la seule bibliothèque standard.

**Le modèle a été faux trois fois avant d'être juste**, et chaque correction a
inversé une conclusion :

1. Une enchère ratée détruisait le collatéral. Faux — une enchère ratée ne détruit
   rien ; le coffre reste ouvert et est remis aux enchères.
2. Un impact de marché linéaire transformait un crash exogène de −50 % en −85 %
   réel, écrasant toute comparaison. Remplacé par la loi d'impact en racine carrée.
3. Le capital des liquidateurs était illimité, donc le système clôturait toujours.
   Ajout d'une contrainte de capacité journalière — ce qui a réellement lâché le
   Jeudi noir.

Avant ces corrections, il annonçait « tout va bien » pour des raisons entièrement
fausses.

### Ce qu'il a ensuite trouvé

**Le protocole gèle, il n'explose pas.** À −95 %, les pertes réalisées de kFIAT sont
*inférieures* à celles de −85 % — parce que les liquidations cessent d'avoir lieu.
591 coffres sur 1000 restent ouverts et sous l'eau. La dette devient latente : 30 %
de la dette totale en médiane, 57 % en p95, non couverte, tokens toujours en
circulation.

Pour un protocole immuable, c'est la propriété critique : **il n'y a personne pour
dégeler**.

**Notre Stability Pool ne fonctionne pas.** Il brûle l'ENRK qu'il détient déjà au
lieu d'acheter, et ses munitions sont libellées dans l'actif qu'il défend. Il ne
peut pas placer d'ordre d'achat sous un prix qui baisse.

**Le Recovery Mode n'aurait pas aidé.** Nous avons modélisé le Recovery Mode de
Liquity comme correctif. Il s'est déclenché 47 jours sur 60 et a amélioré le trou
latent p95 de zéro point — parce qu'il accélère l'*éligibilité* alors que la
défaillance est dans l'*exécution*. Chez Liquity il fonctionne parce qu'un Stability
Pool absorbe les liquidations sans acheteur ; les deux forment une paire.

**Le correctif est un paramètre statique.** Descendre le plancher d'enchère de 85 % à
75 % élimine entièrement le gel — trou latent p95 de 46 % à zéro — pour +2,4 % de
décote supplémentaire en marché calme. Des planchers de 75 %, 70 % et 60 % donnent
des résultats identiques, car une enchère hollandaise se conclut au premier prix
acceptable : une fois le plancher assez profond pour couvrir la demande maximale,
descendre plus bas ne coûte rien. **Le plancher est une soupape de sécurité, pas un
prix.**

**Notre plafond kFIAT de 30 % est un seuil à l'émission, pas une garantie
permanente.** Brûler de l'ENRK réduit le dénominateur, donc la défense du peg et le
plafond tirent en sens inverse. Nous le documentons comme tel plutôt que d'affirmer
le contraire.

---

## 5. Ce que nous ne prétendons pas

- Aucun code n'est déployé. Aucun audit n'a été réalisé.
- Une implémentation Rust antérieure (~5 000 lignes, 119 tests passants) visait le
  mauvais environnement d'exécution et ne se déploie pas. Elle survit comme
  spécification exécutable et oracle de test différentiel, rien de plus.
- La construction d'oracle du §3 est dérivée du texte des KIP et **n'a été validée
  par aucun des auteurs de ces KIP**. C'est la première chose que nous voulons.
- Trois questions de dimensionnement restent ouvertes : le plafond de masse de
  calcul sur le nombre d'entrées, les limites de taille de script SilverScript, et
  l'inclusion en bloc d'une transaction de balayage à plusieurs centaines d'entrées
  (§7.1).
- Le Recovery Mode est indisponible sur L1. D'après le §4 cela ne coûte
  pratiquement rien, mais c'est une différence réelle avec Liquity.
- Être le premier sur ces primitives est un risque, pas un atout. Code immuable, plus
  primitives de trois mois, plus aucun auditeur expérimenté en covenants : nous
  prenons cette combinaison au sérieux.

---

## 6. Ce que l'écosystème y gagne

**Une application phare pour Toccata.** Covenants, identifiants de covenant, actifs
natifs et SilverScript sont sortis en juin. ENRK sollicite KIP-10, KIP-17 et KIP-20
de façon adversariale, en production, avec de la valeur réelle en jeu.

**De l'assurance qualité adversariale gratuite sur les KIP.** Tout ce que nous
trouvons, nous le publions — y compris ce que nous trouvons contre nous, comme le
montre le §4.

**La première méthodologie d'audit de covenants.** Personne n'a audité un système de
covenants SilverScript en vue d'un déploiement immuable. Celui qui le fera en
premier produira la méthodologie, l'outillage et le catalogue de pièges dont
hériteront tous les projets DeFi Kaspa suivants. C'est un bien public que
l'écosystème ne possède pas aujourd'hui.

**Une implémentation de référence.** Entièrement spécifiée, stress-testée, open
source, GPL-3.0, avec l'analyse des défaillances publiée à côté de la conception.

**La démonstration que les covenants L1 peuvent porter de la vraie DeFi.** Kaskad a
choisi Igra EVM. KRON est sur L1 mais c'est un AMM, pas un système de crédit. Un
stablecoin CDP fonctionnel sur covenants serait la démonstration la plus forte
disponible que les primitives de Toccata suffisent à des applications financières
sérieuses.

---

## 7. Ce que nous demandons

### 7.1 D'abord une réponse technique, pas un financement

Quatre questions. N'importe quel développeur cœur peut y répondre, et elles
décident si ce projet continue :

1. **La construction d'oracle du §3 est-elle correcte ?** Précisément : un covenant
   peut-il vérifier de façon fiable `OpInputCovenantId` sur une entrée sœur, et le
   split un-vers-plusieurs préserve-t-il le `covenant_id` sur tous les enfants
   autorisés, comme nous lisons KIP-20 ?
2. **Quel est le plafond de masse de calcul sur le nombre d'entrées**, quand chaque
   entrée exécute un script de covenant ? Cela fixe le N maximal et nous n'avons
   pas pu l'établir.
3. **Quelles sont les limites de taille de script de SilverScript ?** La branche
   usage doit parcourir les entrées pour trouver la lignée du coffre — boucle et
   comparaisons.
4. **Une transaction de balayage à plusieurs centaines d'entrées est-elle
   incluable de façon fiable**, ou sera-t-elle évincée ?

Si la réponse à (1) est non, cette proposition s'arrête et nous déployons ailleurs
ou nous attendons. Nous préférons l'apprendre de vous maintenant que d'un auditeur
dans six mois.

### 7.2 Ensuite, un partenariat d'audit

Deux audits de code et un audit économique, aux prix du marché Solidity de l'ordre
de 40 à 100 k$ par audit de code avant toute prime covenants. Nous cherchons un
soutien de l'écosystème pour cela, et nous le structurerions explicitement pour
éviter tout conflit d'intérêts :

- mandat indépendant, sans droit de regard éditorial d'aucun financeur
- **publication intégrale de chaque rapport quel qu'en soit le résultat**
- idéalement une seconde revue non financée par la même source

Un audit économique importe davantage qu'un second audit de code. Le gel décrit au
§4 est un défaut de conception dans du code parfaitement correct — aucun auditeur de
code ne l'aurait détecté. C'est ainsi que meurent les stablecoins.

### 7.3 Ce que nous ne demandons pas

Aucune allocation de jetons, aucun soutien au listing, aucun marketing, aucun accès
privilégié à un pont, et aucune exception à quelque limite que ce soit du protocole.

---

## 8. État d'avancement

| | |
|---|---|
| Conception économique | Terminée |
| Formule de peg, backtestée | Terminée |
| Stress test de crash, protocole complet | Terminé, publié |
| Construction d'oracle par covenants | Spécifiée, **non validée** |
| Évaluation de la cible d'exécution | Terminée |
| Implémentation | Non commencée |
| Audit | Non commencé |

Tout ce qui est référencé ici se trouve dans le dépôt : les spécifications, le
stress test et ses résultats, l'évaluation de la cible d'exécution avec citations
primaires des KIP, et le journal des décisions de conception que nous avons
inversées.

**https://github.com/cyprox/ENRK_stablecoin**

Licence : GPL-3.0.

**Auteur :** cyprox — développeur unique. Contact via le dépôt.

Le développement est financé par une part plafonnée des frais du protocole, publiée
dans la spécification des paramètres gelés : 20 % des frais vers une adresse de
trésor jusqu'à un plafond cumulé fixe, puis 0 % définitivement, le flux basculant
en permanence vers le protocole. Le plafond est une constante de compilation, son
compteur est lisible on-chain par n'importe qui, et personne ne peut le relever.
C'est indiqué ici plutôt que découvert plus tard, parce qu'un revenu de fondateur
non divulgué est ce qui fait perdre la confiance — non parce qu'en prendre un
serait illégitime.
