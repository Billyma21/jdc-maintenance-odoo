{
    "name": "Maintenance multi-sites",
    "summary": "Sites, contrats de maintenance, interventions, bons d'intervention PDF et rappels d'echeance",
    "description": """
Suivi de la maintenance sur sites clients.

- Sites : aeroport ou plateforme, pays, client, contraintes d'acces.
- Contrats de maintenance : periodicite, prochaine echeance, niveau d'alerte
  calcule (a jour, a planifier, en retard) et planification de la visite suivante.
- Interventions : preventives et correctives, rattachees a un site et a un contrat,
  avec technicien, duree, travail de nuit, etat et rapport detaille.
- Bon d'intervention PDF genere depuis la fiche, avec visa client.
- Rappels automatiques : une action planifiee cree une activite sur les contrats
  dont la visite approche ou est depassee.
- Deux profils d'utilisateurs : Technicien et Responsable.
- Analyse : heures et nombre d'interventions par site, par type et par mois.
""",
    "version": "2.1.0",
    "category": "Services/Field Service",
    "author": "MAAYOUD.B (Bilal Maayoud)",
    "website": "https://github.com/Billyma21/jdc-maintenance-odoo",
    "maintainers": ["Billyma21"],
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/jdc_security.xml",
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/site_views.xml",
        "views/circuit_views.xml",
        "views/contrat_views.xml",
        "views/intervention_views.xml",
        "views/mesure_views.xml",
        "views/campagne_views.xml",
        "views/equipe_views.xml",
        "report/intervention_report.xml",
        "report/site_conformite_report.xml",
        "views/menus.xml",
        "data/cron.xml",
        "data/users_demo.xml",
        "data/demo_equipes.xml",
        "data/demo_sites.xml",
        "data/demo_circuits.xml",
        "data/demo_interventions.xml",
    ],
    "application": True,
    "installable": True,
}
