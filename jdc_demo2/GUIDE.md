# Guide complet - Prototype Odoo de suivi de maintenance

> **Auteur :** MAAYOUD.B - Bilal Maayoud ([@Billyma21](https://github.com/Billyma21))  
> **Copyright © 2026 MAAYOUD.B** - licence LGPL-3.0

Trois parties : **installer**, **mettre aux couleurs de l'entreprise**, **tester comme
un vrai utilisateur**.

---

## 1. Installer, environ 10 minutes

Prérequis : Docker Desktop installé et **démarré** (l'icône baleine doit être active).

```bash
cd jdc_demo2
docker compose up -d
```

Le premier lancement télécharge Odoo et PostgreSQL, comptez quelques minutes.
Vérifier que les deux conteneurs tournent :

```bash
docker compose ps
```

Ouvrir **http://localhost:8069**

1. **Créer la base**
   - Master Password : `admin` (à retenir)
   - Database Name : `demo`
   - Email : `admin` - Password : `admin`
   - Langue : Français (BE), Pays : Belgique
   - **Ne pas cocher** « Load demonstration data » : le module apporte les siennes.

2. **Activer le mode développeur**
   Paramètres → descendre tout en bas → *Activer le mode développeur*.

3. **Installer le module**
   Applications → bouton *Mettre à jour la liste des applications* → Mettre à jour.
   Dans la barre de recherche, **enlever le filtre « Applications »**, taper
   `maintenance`, puis *Installer* sur **Maintenance multi-sites**.

Le menu **Maintenance** apparaît. La base contient déjà 6 sites, 5 contrats et
10 interventions.

---

## 2. Mettre aux couleurs de l'entreprise, 2 minutes

Odoo utilise le nom, le logo et l'adresse de la société dans tous les documents PDF.
Rien à coder, c'est un paramétrage.

1. Paramètres → *Utilisateurs et sociétés* → **Sociétés** → ouvrir la société.
2. Remplacer le nom par celui de l'entreprise.
3. Cliquer sur le carré du logo en haut à gauche et charger l'image.
   Télécharger au préalable le logo depuis leur site, clic droit sur l'image,
   *Enregistrer l'image sous*.
4. Compléter l'adresse, le téléphone, le site web, la TVA.
5. Enregistrer.

Rouvrir une intervention → *Imprimer* → **Bon d'intervention** : le PDF sort
avec l'en-tête et le pied de page de l'entreprise.

Pour la couleur de l'interface : Paramètres → *Personnalisation* → thème, ou
simplement garder le thème par défaut, c'est plus sobre en entretien.

> À dire pendant la démonstration : « Le logo et l'en-tête viennent de la fiche
> société d'Odoo, donc tous les documents suivent automatiquement. Je n'ai rien
> codé en dur. » C'est exactement le réflexe qu'on attend de quelqu'un qui
> paramètre un ERP.

---

## 3. Tester comme un vrai utilisateur

Le module crée **deux comptes** avec des droits différents. C'est ce qui permet de
montrer que l'outil est utilisable par une équipe, pas seulement par toi.

| Compte | Login | Mot de passe | Ce qu'il peut faire |
|---|---|---|---|
| Technicien terrain | `technicien` | `technicien` | Voit les sites et contrats en lecture, crée et complète ses interventions, ne peut rien supprimer |
| Responsable maintenance | `responsable` | `responsable` | Tout, plus le menu Analyse |
| Administrateur | `admin` | `admin` | Administration complète d'Odoo |

**Pour basculer de compte :** ouvrir une fenêtre de navigation privée sur
http://localhost:8069 et se connecter avec l'autre login. Tu peux ainsi avoir
deux sessions côte à côte, technicien d'un côté, responsable de l'autre.

### Scénario de test complet, 10 minutes

**En tant que responsable** (`responsable` / `responsable`)

1. **Maintenance → Contrats → À planifier.**
   Une ligne rouge (visite en retard), deux oranges (visite sous 30 jours).
   La couleur est calculée, pas saisie.
2. Ouvrir le contrat en retard → bouton **Planifier la prochaine visite**.
   Une intervention est créée automatiquement et l'échéance du contrat est
   décalée selon la périodicité. Revenir aux contrats : la ligne n'est plus rouge.
3. **Maintenance → Analyse.** Vue pivot : heures par site et par type.
   Basculer en vue graphique en haut à droite.

**En tant que technicien** (`technicien` / `technicien`, en navigation privée)

4. **Maintenance → Interventions → Mes interventions.**
   Seules les siennes apparaissent. Vue kanban groupée par état :
   les cartes se déplacent d'une colonne à l'autre à la souris.
5. Ouvrir une intervention planifiée → **Démarrer** → remplir *Travaux réalisés*,
   *Constat*, *Suite à donner*, le visa client → **Terminer**.
6. Essayer de supprimer l'intervention : **impossible**, le droit n'est pas accordé.
   C'est volontaire.
7. Aller dans **Sites** : lecture seule, pas de bouton *Nouveau*.

**Le document**

8. Sur une intervention terminée : **Imprimer → Bon d'intervention**.
   PDF avec l'en-tête de la société et les deux cases de signature.

**Les rappels automatiques**

9. En tant qu'administrateur, mode développeur actif :
   Paramètres → *Technique* → *Actions planifiées* → chercher
   « rappel des échéances » → bouton **Exécuter manuellement**.
10. Retourner sur un contrat dont la visite approche : une **activité** apparaît
    dans le chatter, avec la date d'échéance. En production, cette action tourne
    une fois par jour, toute seule.

---

## Au quotidien

**Après une modification du code**
```bash
docker compose restart odoo
```
puis Applications → chercher le module → **Mettre à niveau**.
Un XML modifié n'est pris en compte qu'après la mise à niveau : les vues Odoo
sont des *données* chargées en base, pas du code relu à chaud.

**Voir les erreurs**
```bash
docker compose logs -f odoo
```

**Arrêter** : `docker compose down`
**Repartir de zéro** : `docker compose down -v` puis `docker compose up -d`

---

## Si ça coince

| Symptôme | Cause la plus fréquente |
|---|---|
| Le module n'apparaît pas dans Applications | Mode développeur non activé, liste des applications non mise à jour, ou filtre « Applications » encore actif dans la recherche |
| Erreur au moment d'installer | `docker compose logs -f odoo` donne le fichier et la ligne exacte |
| Le PDF ne se génère pas | wkhtmltopdf est inclus dans l'image `odoo:17`. Si le rendu échoue, la liste et le formulaire suffisent pour la démonstration |
| Page blanche après installation | Rafraîchir avec Ctrl+F5, le cache des assets |
| Le port 8069 est déjà pris | Changer `"8069:8069"` en `"8070:8069"` dans docker-compose.yml |

---

## Ce qu'il faut savoir expliquer

- Un **modèle** Odoo est une classe Python héritant de `models.Model` ; chaque
  `fields.X` devient une colonne PostgreSQL via l'ORM.
- Les **vues** sont en XML et sont des données chargées à l'installation.
- Sans ligne dans `ir.model.access.csv`, le modèle existe mais personne ne peut
  le lire. Ici il y a deux lignes par modèle, une par groupe.
- Les **groupes** sont définis dans `security/jdc_security.xml` ; Responsable
  *implique* Technicien, donc il hérite de ses droits.
- `alerte` est un champ **calculé non stocké**. Pour pouvoir filtrer dessus, il
  faut lui fournir une méthode `search`, c'est `_search_alerte`.
- L'**action planifiée** (`ir.cron`) appelle une méthode Python du modèle une
  fois par jour et crée une activité, sans doublon.
- Le **bon d'intervention** est un template **QWeb**, du XML avec des directives
  `t-field`, qui réutilise `web.external_layout` pour l'en-tête société.

---

## La suite, si le projet devenait réel

- **Saisie terrain hors ligne.** Sur une piste, la connectivité est mauvaise et
  les créneaux courts. Un formulaire qui fonctionne sans réseau et se synchronise
  au retour, plutôt qu'une ressaisie le lendemain.
- **Équipements et pièces.** Rattacher l'intervention aux feux, armoires et
  régulateurs concernés, suivre les pièces consommées.
- **Détection des récurrences.** Repérer les équipements qui reviennent trop
  souvent en correctif : c'est là que se cache le vrai coût.
- **Mesures et conformité.** Importer les relevés, pré-remplir le dossier,
  les seuils restant paramétrables.
- **Signature sur tablette** directement sur le bon d'intervention.
