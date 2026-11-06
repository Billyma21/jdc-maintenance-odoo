# Maintenance multi-sites - Odoo 17

[![Odoo](https://img.shields.io/badge/Odoo-17.0-714B67?logo=odoo&logoColor=white)](https://www.odoo.com/)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3.0-blue.svg)](./LICENSE)
[![Author](https://img.shields.io/badge/Author-MAAYOUD.B-0A66C2)](https://github.com/Billyma21)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](./jdc_demo2/docker-compose.yml)

Prototype professionnel de **suivi de maintenance multi-sites** pour le balisage lumineux aéronautique (AGL), construit sur **Odoo 17**.

> **Auteur :** MAAYOUD.B - Bilal Maayoud ([@Billyma21](https://github.com/Billyma21))  
> **Copyright © 2026 MAAYOUD.B** - distribué sous licence **LGPL-3.0**  
> Voir [`COPYRIGHT`](./COPYRIGHT) et [`LICENSE`](./LICENSE).

---

## Présentation

Ce dépôt contient une application Odoo complète pour piloter :

| Domaine | Contenu |
|---|---|
| **Sites** | Aéroports / plateformes, code OACI, client, contraintes d’accès |
| **Circuits** | Balisage (annexe 14), disponibilité, isolement, conformité |
| **Contrats** | Périodicité, échéances, alertes calculées, planification |
| **Interventions** | Préventives / correctives, assignation, kanban, rapport terrain |
| **Relevés** | Visuel, isolement (MΩ), électrique, photométrie + graphiques |
| **Bons PDF** | Bon d’intervention + attestation de conformité + photo du bon signé |
| **Équipes** | Admin → responsables → techniciens (droits et messages) |

Conçu pour une démonstration client claire : le **responsable** planifie et assigne, le **technicien** exécute et confirme, l’**administrateur** configure les équipes.

---

## Tutoriel d’utilisation

Regardez le parcours technicien (connexion → mission → relevés → bon PDF → photo signée → confirmation) :

| Support | Lien |
|---|---|
| **Vidéo tuto** (MP4, ~32 Mo) | [docs/JDC_Tuto_Technicien.mp4](./docs/JDC_Tuto_Technicien.mp4) |
| **Manuel PDF** - Guide des interventions | [docs/Guide_des_interventions.pdf](./docs/Guide_des_interventions.pdf) |

> Sur GitHub : ouvrez la vidéo puis cliquez **View raw** / le lecteur intégré pour la lire dans le navigateur.  
> Téléchargement direct aussi disponible dans les [Releases](https://github.com/Billyma21/jdc-maintenance-odoo/releases).

<details>
<summary><strong>Aperçu du contenu du tuto</strong></summary>

1. Connexion avec le compte technicien  
2. Ouverture d’une intervention assignée  
3. Saisie des relevés terrain  
4. Impression du bon d’intervention  
5. Ajout de la photo du bon signé  
6. Confirmation et retour d’info au responsable  

</details>

---

## Structure du dépôt

```
Project-jdc_maintenance/
├── README.md                 ← ce fichier
├── LICENSE                   ← LGPL-3.0
├── COPYRIGHT                 ← copyright Bilal Maayoud
├── .gitignore
├── docs/                     ← vidéo tuto + manuel PDF
├── Formation_Technicien/     ← notes formation (archives locales hors git)
└── jdc_demo2/
    ├── docker-compose.yml    ← Odoo 17 + PostgreSQL 15
    ├── README.md
    ├── GUIDE.md              ← installation & parcours de test
    └── addons/
        └── jdc_maintenance/  ← module Odoo
```

---

## Démarrage rapide

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré

### Lancer

```bash
cd jdc_demo2
docker compose up -d
```

Ouvrir **http://localhost:8069**

### Première installation

1. Créer une base (ex. `demo`) - **ne pas** cocher les données de démonstration Odoo  
2. Activer le **mode développeur** (Paramètres → bas de page)  
3. Applications → **Mettre à jour la liste** → chercher `Maintenance multi-sites` → **Installer**

Le menu **Maintenance** apparaît avec le jeu de données de démonstration du module.

### Comptes de démonstration

| Rôle | Identifiant | Mot de passe |
|---|---|---|
| Administrateur | `admin` | `admin` |
| Responsable | `responsable` | `responsable` |
| Technicien | `technicien` | `technicien` |

---

## Rôles & responsabilités

```
Administrateur
  └── configure les équipes (qui manage qui)
Responsable
  └── crée les missions et assigne un technicien de son équipe
Technicien
  └── reçoit ses missions, complète, imprime le bon, joint la photo signée
      (ne crée pas d’intervention)
```

Les messages du chatter envoyés par le technicien notifient le responsable abonné à la mission.

---

## Fonctionnalités clés

- **Vue d’ensemble** kanban des sites (OK / vigilance / critique)
- **Points de vigilance** : non-conformité, isolement sous seuil, défaillances récurrentes
- **Graphique d’isolement** (ex. dérive 142 → 89 → 38 MΩ)
- **Bon d’intervention PDF** + confirmation par photo du document signé
- **Attestation de conformité** PDF par site
- **Saisie rapide de campagne** de relevés
- **Analyse** pivot / graphiques (responsable)
- Seuils de disponibilité et d’isolement **paramétrables** (aucune valeur réglementaire inventée en dur)

---

## Stack technique

| Composant | Version |
|---|---|
| Odoo | 17 |
| PostgreSQL | 15 |
| Dépendances module | `base`, `mail` uniquement |
| Conteneurisation | Docker Compose |
| Licence module | LGPL-3 |

---

## Documentation

| Document | Description |
|---|---|
| [`docs/JDC_Tuto_Technicien.mp4`](./docs/JDC_Tuto_Technicien.mp4) | Tutoriel vidéo d’utilisation (technicien) |
| [`docs/Guide_des_interventions.pdf`](./docs/Guide_des_interventions.pdf) | Manuel PDF - guide des interventions |
| [`jdc_demo2/GUIDE.md`](./jdc_demo2/GUIDE.md) | Installation, branding société, scénarios de test |
| [`jdc_demo2/README.md`](./jdc_demo2/README.md) | Présentation métier du prototype |
| [`Formation_Technicien/README.md`](./Formation_Technicien/README.md) | Supports de formation |
| [`COPYRIGHT`](./COPYRIGHT) | Mentions d’auteur et de copyright |
| [`LICENSE`](./LICENSE) | Texte de la licence LGPL-3.0 |

---

## Auteur

**MAAYOUD.B** - Bilal Maayoud  
GitHub : [@Billyma21](https://github.com/Billyma21)

```
Copyright (c) 2026 MAAYOUD.B (Bilal Maayoud)
Licensed under the GNU Lesser General Public License v3.0
```

Ce projet a été conçu, développé et documenté uniquement par **MAAYOUD.B**.  
Toute réutilisation doit respecter la licence LGPL-3.0 et conserver les mentions d’auteur.

---

## Commandes utiles

```bash
# État des conteneurs
docker compose -f jdc_demo2/docker-compose.yml ps

# Logs Odoo
docker compose -f jdc_demo2/docker-compose.yml logs -f odoo

# Redémarrage après modification du code
docker compose -f jdc_demo2/docker-compose.yml restart odoo
# puis dans Odoo : Applications → Maintenance multi-sites → Mettre à niveau

# Reset complet (efface la base)
docker compose -f jdc_demo2/docker-compose.yml down -v
docker compose -f jdc_demo2/docker-compose.yml up -d
```

---

<p align="center">
  <sub>Made by <strong>MAAYOUD.B</strong> · <a href="https://github.com/Billyma21">github.com/Billyma21</a> · © 2026</sub>
</p>
