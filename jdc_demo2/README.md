# Prototype Odoo — Suivi de la maintenance multi-sites

> **Auteur :** MAAYOUD.B — Bilal Maayoud ([@Billyma21](https://github.com/Billyma21))  
> **Copyright © 2026 MAAYOUD.B** — licence LGPL-3.0

Prototype monté pour l'entretien chez JDC Airports, à partir de la fiche de fonction
qui mentionne Odoo comme outil de gestion de l'entreprise.

L'idée : la maintenance de balisage repose sur des **contrats périodiques** par site,
exécutés par des **interventions** préventives ou correctives, qui doivent produire un
**bon d'intervention signé par le client**. Le prototype modélise ces trois objets et
la chose qui coûte le plus cher quand elle est oubliée : **l'échéance d'une visite**.

## Ce que ça fait

**Sites.** Aéroport ou plateforme, code OACI, pays, client, contact, et un champ
« accès et contraintes » pour le badge, l'escorte et les créneaux de nuit. Compteurs
d'interventions et d'heures par site.

**Contrats de maintenance.** Périodicité mensuelle à annuelle, date de prochaine visite,
et surtout un **niveau d'alerte calculé** : à jour, à planifier sous 30 jours, en retard.
La liste se colore toute seule, orange puis rouge. Un menu « À planifier » n'affiche que
ce qui brûle. Le bouton « Planifier la prochaine visite » crée l'intervention et décale
automatiquement l'échéance selon la périodicité.

**Interventions.** Préventive ou corrective, rattachées au site et au contrat, avec
technicien, durée, indicateur de travail de nuit, et un rapport en trois parties :
travaux réalisés, constat et anomalies, suite à donner. Cycle planifiée → en cours →
terminée. Historique et suivi via le chatter Odoo.

**Bon d'intervention PDF.** Généré depuis la fiche, avec les deux cases de signature,
intervenant et visa client.

**Analyse.** Vues pivot et graphique : heures et nombre d'interventions par site, par
type, par mois. Vue calendrier pour le planning.

**Jeu de données de démonstration** chargé à l'installation : 6 sites, 5 contrats dont
un en retard et deux à planifier, 10 interventions réparties sur les derniers mois.
L'écran n'est jamais vide.

## La couche métier : circuits de balisage et relevés

C'est la partie qui distingue ce prototype d'un suivi d'interventions générique.

**Circuits de balisage.** Chaque site porte ses circuits série, repérés par leur
désignation d'exploitation (07R/25L axe, bretelle W, barres d'arrêt). Pour chacun :
le **système** au vocabulaire de l'annexe 14 (axe de piste, bord de piste, seuil,
extrémité, TDZ, rampe d'approche, PAPI, axe et bord de voie de circulation, barres
d'arrêt, balisage d'obstacles), la **catégorie d'approche** desservie (CAT I à III),
le **régulateur à courant constant** avec sa puissance, son **intensité nominale**
(6,6 A par défaut) et son nombre de crans.

**Disponibilité et conformité.** Nombre de feux, nombre de feux hors service, taux
de disponibilité calculé, et un verdict automatique : conforme, sous surveillance,
non conforme. **Le seuil est un champ paramétrable, pas une constante codée en dur**,
parce qu'il dépend du système et de la catégorie et qu'il se confirme avec
l'exploitant. Un menu « Points de vigilance » regroupe tout ce qui sort des clous.

**Relevés de contrôle.** Les contrôles périodiques du guide de maintenance :
inspection visuelle mensuelle, **mesure d'isolement semestrielle** en MΩ, contrôle
électrique annuel, relevé photométrique. Chaque relevé porte le courant mesuré,
l'écart au nominal calculé automatiquement, la valeur d'isolement, le nombre de feux
hors service et les observations. **Le dernier relevé remonte tout seul sur la fiche
du circuit**, et une vue graphique montre l'évolution de l'isolement dans le temps.

**Sécurité électrique sur l'intervention.** Habilitation requise au sens de la
NF C18-510 (B2V, BR) et case de consignation du circuit avant travaux.

### Ce que raconte le jeu de démonstration

1 680 feux répartis sur 15 circuits et 6 sites, 45 hors service, soit 97,3 % de
disponibilité globale. Trois circuits sortent des clous, et chacun raconte une
histoire différente :

- **TDZ de Bruxelles, CAT III.** L'isolement passe de 142 à 89 puis à 38 MΩ sur trois
  campagnes, pendant que les feux hors service montent de 1 à 7. Ce n'est pas une
  panne, c'est une dérive. La vue graphique des relevés la rend visible d'un coup d'œil.
- **Barres d'arrêt de Liège.** Troisième épisode correctif en huit mois sur le même
  circuit. Le symptôme est traité à chaque fois, la cause jamais.
- **Bretelle W de Paris.** Isolement sous le seuil, circuit maintenu en service sous
  surveillance renforcée en attendant la recherche de défaut.

C'est exactement le genre de signal qu'un tableau fait apparaître et qu'un classeur
de fiches papier noie.

### D'où vient le vocabulaire

Annexe 14 de l'OACI pour les systèmes de balisage et les catégories d'approche,
guide de maintenance du balisage lumineux des aérodromes du STAC pour les contrôles
périodiques et leurs périodicités, NF EN 61821 pour la maintenance des installations
électriques de balisage, NF C18-510 pour les habilitations électriques.

**Je ne prétends pas connaître les seuils réglementaires applicables à chaque système.**
C'est précisément pour ça qu'ils sont paramétrables : les valeurs se définissent avec
l'exploitant et selon le contrat, et un chiffre codé en dur dans une application est
un piège.

## Lancer

Prérequis : Docker Desktop installé et démarré.

```bash
cd jdc_demo2
docker compose up -d
```

Navigateur : http://localhost:8069

1. Créer une base. Mot de passe maître au choix. **Ne pas cocher** « charger les
   données de démonstration » : le module apporte les siennes.
2. Paramètres → tout en bas → Activer le mode développeur.
3. Applications → « Mettre à jour la liste des applications ».
4. Retirer le filtre « Applications » dans la barre de recherche, chercher
   `maintenance multi-sites`, installer.

Le menu **Maintenance** apparaît en haut.

## Après une modification du code

```bash
docker compose restart odoo
```
Puis Applications → chercher le module → **Mettre à niveau**.

Un XML modifié n'est pris en compte qu'après la mise à niveau : les vues Odoo sont
des **données** chargées en base, pas du code lu à chaud.

## Parcours de démonstration, 3 minutes

1. **Contrats → À planifier.** Une ligne rouge, deux oranges. « Voilà l'écran que
   j'ouvrirais le lundi matin. »
2. Ouvrir le contrat en retard, cliquer **Planifier la prochaine visite**.
   L'intervention est créée et l'échéance se décale automatiquement.
3. Remplir le rapport, **Démarrer**, **Terminer**, puis **Imprimer → Bon d'intervention**.
   Le PDF sort avec les cases de signature.
4. **Analyse.** Pivot heures par site et par type. « Trois correctives sur le même
   circuit en huit mois, c'est ce genre de chose que le tableau fait ressortir. »

## Si ça coince

- **Le module n'apparaît pas** : mode développeur non activé, ou liste des applications
  non mise à jour, ou filtre « Applications » encore actif dans la recherche.
- **Erreur au chargement d'un XML** : `docker compose logs -f odoo` donne la ligne exacte.
- **Le PDF ne sort pas** : wkhtmltopdf est inclus dans l'image officielle `odoo:17`.
  Si le rendu échoue, la liste et le formulaire suffisent pour la démonstration.
- **Repartir de zéro** : `docker compose down -v` puis `docker compose up -d`.

## Ce que j'expliquerais sur la structure

- Un modèle Odoo est une **classe Python** héritant de `models.Model` ; chaque
  `fields.X` devient une colonne PostgreSQL via l'**ORM**.
- Les **vues sont en XML** et sont des données chargées à l'installation.
- Sans ligne dans `ir.model.access.csv`, le modèle existe mais personne ne peut le lire.
- `@api.depends` déclare de quoi dépend un champ calculé ; `alerte` est calculé et non
  stocké, donc il faut lui fournir une méthode `search` pour pouvoir filtrer dessus.
- `@api.model_create_multi` est la signature moderne de la création en lot.
- Une **séquence** `ir.sequence` génère les références côté serveur, ce qui évite les
  doublons en cas de création simultanée.
- Les boutons du `<header>` appellent des **méthodes Python** du modèle via `type="object"`.
- Le rapport PDF est un **template QWeb**, du XML avec des directives `t-field`.

## Ce que j'ajouterais ensuite

- **Saisie terrain hors ligne.** Sur une piste, la connectivité est mauvaise et les
  créneaux sont courts. Un formulaire qui fonctionne sans réseau et se synchronise au
  retour, plutôt qu'un technicien qui ressaisit tout le lendemain.
- **Équipements et pièces.** Rattacher l'intervention aux feux, armoires et régulateurs
  concernés, et suivre les pièces consommées.
- **Détection des récurrences.** Repérer automatiquement les équipements ou circuits
  qui reviennent trop souvent en correctif : c'est là que se cache le vrai coût.
- **Mesures et conformité.** Importer les relevés et pré-remplir le dossier de
  conformité, les seuils restant paramétrables.
- **Rappels automatiques** sur les échéances de contrat, par activité Odoo ou par mail.
