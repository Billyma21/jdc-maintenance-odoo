# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

# Nombre de mois correspondant a chaque periodicite.
MOIS_PAR_PERIODICITE = {
    "mensuelle": 1,
    "trimestrielle": 3,
    "semestrielle": 6,
    "annuelle": 12,
}


class JdcContrat(models.Model):
    """Un contrat de maintenance preventive sur un site."""

    _name = "jdc.contrat"
    _description = "Contrat de maintenance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_prochaine asc, id desc"

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau",
    )
    site_id = fields.Many2one("jdc.site", string="Site", required=True, ondelete="restrict")
    partner_id = fields.Many2one(related="site_id.partner_id", string="Client", store=True, readonly=True)
    date_debut = fields.Date(string="Début", required=True, default=fields.Date.context_today)
    date_fin = fields.Date(string="Fin")
    periodicite = fields.Selection(
        selection=[
            ("mensuelle", "Mensuelle"),
            ("trimestrielle", "Trimestrielle"),
            ("semestrielle", "Semestrielle"),
            ("annuelle", "Annuelle"),
        ],
        string="Périodicité",
        default="trimestrielle",
        required=True,
    )
    date_prochaine = fields.Date(string="Prochaine visite")
    etat = fields.Selection(
        selection=[
            ("brouillon", "Brouillon"),
            ("actif", "Actif"),
            ("suspendu", "Suspendu"),
            ("cloture", "Clôturé"),
        ],
        string="État",
        default="brouillon",
        required=True,
    )
    notes = fields.Text(string="Notes")

    intervention_ids = fields.One2many("jdc.intervention", "contrat_id", string="Interventions")
    intervention_count = fields.Integer(string="Interventions", compute="_compute_intervention_count")

    jours_restants = fields.Integer(
        string="Jours avant visite",
        compute="_compute_jours_restants",
        help="Négatif si la visite est en retard.",
    )
    alerte = fields.Selection(
        selection=[
            ("ok", "À jour"),
            ("bientot", "À planifier"),
            ("retard", "En retard"),
        ],
        string="Alerte",
        compute="_compute_jours_restants",
        search="_search_alerte",
    )

    @api.depends("intervention_ids")
    def _compute_intervention_count(self):
        for contrat in self:
            contrat.intervention_count = len(contrat.intervention_ids)

    @api.depends("date_prochaine")
    def _compute_jours_restants(self):
        """Calcule le delai avant la prochaine visite et le niveau d'alerte."""
        aujourdhui = fields.Date.context_today(self)
        for contrat in self:
            if not contrat.date_prochaine:
                contrat.jours_restants = 0
                contrat.alerte = "ok"
                continue
            delta = (contrat.date_prochaine - aujourdhui).days
            contrat.jours_restants = delta
            if delta < 0:
                contrat.alerte = "retard"
            elif delta <= 30:
                contrat.alerte = "bientot"
            else:
                contrat.alerte = "ok"

    def _search_alerte(self, operator, value):
        """Permet de filtrer sur un champ calcule non stocke."""
        aujourdhui = fields.Date.context_today(self)
        dans_30_jours = aujourdhui + relativedelta(days=30)
        if operator not in ("=", "!="):
            return []
        domaines = {
            "retard": [("date_prochaine", "<", aujourdhui)],
            "bientot": [
                ("date_prochaine", ">=", aujourdhui),
                ("date_prochaine", "<=", dans_30_jours),
            ],
            "ok": [("date_prochaine", ">", dans_30_jours)],
        }
        domaine = domaines.get(value, [])
        if not domaine:
            return []
        if operator == "!=":
            if len(domaine) > 1:
                domaine = ["&"] + domaine
            return ["!"] + domaine
        return domaine

    @api.onchange("date_debut", "periodicite")
    def _onchange_planification(self):
        """Propose une prochaine visite coherente avec la periodicite."""
        if self.date_debut and self.periodicite and not self.date_prochaine:
            mois = MOIS_PAR_PERIODICITE.get(self.periodicite, 3)
            self.date_prochaine = self.date_debut + relativedelta(months=mois)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "Nouveau":
                vals["name"] = self.env["ir.sequence"].next_by_code("jdc.contrat") or "CTR-0001"
        return super().create(vals_list)

    def action_activer(self):
        self.write({"etat": "actif"})

    def action_cloturer(self):
        self.write({"etat": "cloture"})

    def action_planifier_visite(self):
        """Cree une intervention preventive a la date prevue et decale l'echeance."""
        self.ensure_one()
        mois = MOIS_PAR_PERIODICITE.get(self.periodicite, 3)
        date_visite = self.date_prochaine or fields.Date.context_today(self)
        intervention = self.env["jdc.intervention"].create({
            "site_id": self.site_id.id,
            "contrat_id": self.id,
            "date_intervention": date_visite,
            "type_intervention": "preventive",
            "technicien_id": False,
            "description": "Visite périodique au titre du contrat %s." % self.name,
        })
        self.date_prochaine = date_visite + relativedelta(months=mois)
        return {
            "type": "ir.actions.act_window",
            "name": "Visite planifiée — à assigner",
            "res_model": "jdc.intervention",
            "res_id": intervention.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def _cron_rappel_echeances(self, jours=15):
        """Crée une activité de rappel sur les contrats dont la visite approche.

        Appelé par l'action planifiée. Ne crée pas de doublon : un contrat qui a
        déjà une activité ouverte est ignoré.
        """
        limite = fields.Date.context_today(self) + relativedelta(days=jours)
        contrats = self.search([
            ("etat", "=", "actif"),
            ("date_prochaine", "!=", False),
            ("date_prochaine", "<=", limite),
        ])
        cree = 0
        for contrat in contrats:
            if contrat.activity_ids:
                continue
            retard = contrat.date_prochaine < fields.Date.context_today(self)
            contrat.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=contrat.date_prochaine,
                summary="Visite %s - %s" % (
                    "EN RETARD" if retard else "à planifier",
                    contrat.site_id.name,
                ),
                note="Visite %s prévue le %s au titre du contrat %s." % (
                    contrat.periodicite,
                    contrat.date_prochaine,
                    contrat.name,
                ),
            )
            cree += 1
        return cree

    def action_voir_interventions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Interventions - %s" % self.name,
            "res_model": "jdc.intervention",
            "view_mode": "tree,form",
            "domain": [("contrat_id", "=", self.id)],
            "context": {
                "default_contrat_id": self.id,
                "default_site_id": self.site_id.id,
            },
        }
