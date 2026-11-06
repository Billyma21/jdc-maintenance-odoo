# -*- coding: utf-8 -*-
from odoo import api, fields, models


class JdcSite(models.Model):
    """Un site client : aeroport, heliport ou plateforme."""

    _name = "jdc.site"
    _description = "Site client"
    _order = "name"

    name = fields.Char(string="Site", required=True)
    code = fields.Char(string="Code OACI / IATA", help="Par exemple EBBR, LFPG.")
    country_id = fields.Many2one("res.country", string="Pays")
    partner_id = fields.Many2one("res.partner", string="Client")
    contact = fields.Char(string="Contact sur site")
    telephone = fields.Char(string="Téléphone")
    acces_particulier = fields.Text(
        string="Accès et contraintes",
        help="Badge, escorte, créneaux d'intervention autorisés, travail de nuit.",
    )
    active = fields.Boolean(string="Actif", default=True)

    categorie_max = fields.Selection(
        selection=[
            ("na", "Non applicable"),
            ("cat1", "CAT I"),
            ("cat2", "CAT II"),
            ("cat3", "CAT III"),
        ],
        string="Catégorie d'approche la plus exigeante",
        default="na",
    )

    circuit_ids = fields.One2many("jdc.circuit", "site_id", string="Circuits")
    contrat_ids = fields.One2many("jdc.contrat", "site_id", string="Contrats")
    intervention_ids = fields.One2many("jdc.intervention", "site_id", string="Interventions")

    circuit_count = fields.Integer(string="Circuits", compute="_compute_counts")
    feux_hs_total = fields.Integer(string="Feux hors service", compute="_compute_counts")
    contrat_count = fields.Integer(string="Contrats", compute="_compute_counts")
    intervention_count = fields.Integer(string="Interventions", compute="_compute_counts")
    heures_total = fields.Float(string="Heures totales", compute="_compute_counts")

    nb_feux_total = fields.Integer(
        string="Nombre de feux",
        compute="_compute_indicateurs",
        store=True,
    )
    taux_disponibilite = fields.Float(
        string="Disponibilité (%)",
        compute="_compute_indicateurs",
        store=True,
        digits=(5, 1),
    )
    nb_circuits_non_conformes = fields.Integer(
        string="Circuits non conformes",
        compute="_compute_indicateurs",
        store=True,
    )
    etat_site = fields.Selection(
        selection=[
            ("ok", "OK"),
            ("vigilance", "Vigilance"),
            ("critique", "Critique"),
        ],
        string="État du site",
        compute="_compute_indicateurs",
        store=True,
        help="Critique si au moins un circuit est non conforme. "
             "Vigilance si au moins un circuit est sous surveillance ou si un isolement "
             "est sous le seuil paramétré sur le circuit. Sinon OK.",
    )

    @api.depends(
        "circuit_ids.nb_feux",
        "circuit_ids.nb_feux_hs",
        "circuit_ids.conformite",
        "circuit_ids.isolement_alerte",
    )
    def _compute_indicateurs(self):
        """Disponibilité globale et niveau d'alerte du site, à partir des circuits."""
        for site in self:
            circuits = site.circuit_ids
            nb_feux = sum(circuits.mapped("nb_feux"))
            feux_hs = sum(circuits.mapped("nb_feux_hs"))
            site.nb_feux_total = nb_feux
            if nb_feux <= 0:
                site.taux_disponibilite = 0.0
            else:
                site.taux_disponibilite = (nb_feux - feux_hs) / nb_feux * 100.0
            non_conformes = circuits.filtered(lambda c: c.conformite == "non_conforme")
            site.nb_circuits_non_conformes = len(non_conformes)
            if non_conformes:
                site.etat_site = "critique"
            elif circuits.filtered(lambda c: c.conformite == "surveillance" or c.isolement_alerte):
                site.etat_site = "vigilance"
            else:
                site.etat_site = "ok"

    def _derniers_releves_isolement(self, limite=3):
        """Les derniers relevés d'isolement du site, du plus récent au plus ancien."""
        self.ensure_one()
        return self.env["jdc.mesure"].search([
            ("site_id", "=", self.id),
            ("type_controle", "=", "isolement"),
        ], order="date desc, id desc", limit=limite)

    @api.depends("contrat_ids", "intervention_ids", "intervention_ids.duree",
                 "circuit_ids", "circuit_ids.nb_feux_hs")
    def _compute_counts(self):
        for site in self:
            site.contrat_count = len(site.contrat_ids)
            site.circuit_count = len(site.circuit_ids)
            site.feux_hs_total = sum(site.circuit_ids.mapped("nb_feux_hs"))
            site.intervention_count = len(site.intervention_ids)
            site.heures_total = sum(site.intervention_ids.mapped("duree"))

    def action_saisie_campagne(self):
        """Ouvre l'assistant de campagne prérempli avec les circuits du site."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Saisie rapide de campagne",
            "res_model": "jdc.campagne",
            "view_mode": "form",
            "target": "new",
            "context": {"default_site_id": self.id},
        }

    def action_voir_interventions(self):
        """Ouvre la liste des interventions du site."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Interventions - %s" % self.name,
            "res_model": "jdc.intervention",
            "view_mode": "tree,form",
            "domain": [("site_id", "=", self.id)],
            "context": {"default_site_id": self.id},
        }
