
# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

# Systemes de balisage, vocabulaire de l'annexe 14 de l'OACI.
SYSTEMES = [
    ("axe_piste", "Axe de piste"),
    ("bord_piste", "Bord de piste"),
    ("seuil", "Seuil"),
    ("extremite", "Extrémité de piste"),
    ("tdz", "Zone de toucher des roues (TDZ)"),
    ("approche", "Rampe d'approche"),
    ("papi", "PAPI"),
    ("taxiway_axe", "Axe de voie de circulation"),
    ("taxiway_bord", "Bord de voie de circulation"),
    ("barre_arret", "Barres d'arrêt"),
    ("obstacles", "Balisage d'obstacles"),
]


class JdcCircuit(models.Model):
    """Un circuit série de balisage, alimenté par un régulateur à courant constant."""

    _name = "jdc.circuit"
    _description = "Circuit de balisage"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "site_id, systeme, name"

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau",
    )
    site_id = fields.Many2one("jdc.site", string="Site", required=True, ondelete="cascade")
    designation = fields.Char(string="Désignation", help="Repère d'exploitation, par exemple 07L/25R axe.")
    systeme = fields.Selection(SYSTEMES, string="Système", required=True, default="bord_piste")
    categorie = fields.Selection(
        selection=[
            ("na", "Non applicable"),
            ("cat1", "CAT I"),
            ("cat2", "CAT II"),
            ("cat3", "CAT III"),
        ],
        string="Catégorie d'approche",
        default="na",
        required=True,
    )

    # Regulateur a courant constant
    regulateur = fields.Char(string="Régulateur (CCR)", help="Identifiant du régulateur à courant constant.")
    puissance_kva = fields.Float(string="Puissance (kVA)")
    intensite_nominale = fields.Float(
        string="Intensité nominale (A)",
        default=6.6,
        help="Les circuits série de balisage fonctionnent usuellement à 6,6 A.",
    )
    nb_crans = fields.Integer(string="Crans d'intensité", default=5)

    # Etat du circuit
    nb_feux = fields.Integer(string="Nombre de feux")
    nb_feux_hs = fields.Integer(string="Feux hors service", tracking=True)
    taux_disponibilite = fields.Float(
        string="Disponibilité (%)",
        compute="_compute_disponibilite",
        store=True,
        digits=(5, 1),
    )
    seuil_disponibilite = fields.Float(
        string="Seuil de disponibilité (%)",
        default=95.0,
        help="Valeur contractuelle ou réglementaire applicable à ce système. "
             "À confirmer avec l'exploitant : elle dépend du système et de la catégorie d'approche.",
    )
    conformite = fields.Selection(
        selection=[
            ("na", "Non évalué"),
            ("conforme", "Conforme"),
            ("surveillance", "Sous surveillance"),
            ("non_conforme", "Non conforme"),
        ],
        string="Conformité",
        compute="_compute_disponibilite",
        store=True,
        tracking=True,
    )

    # Mesure d'isolement, controle semestriel du guide de maintenance
    isolement_mohm = fields.Float(string="Dernier isolement (MΩ)", digits=(10, 1), tracking=True)
    date_isolement = fields.Date(string="Date de la mesure")
    seuil_isolement = fields.Float(
        string="Seuil d'isolement (MΩ)",
        help="Laisser à zéro tant que la valeur n'est pas définie : elle dépend de la tension "
             "de mesure et de l'environnement du circuit.",
    )
    isolement_alerte = fields.Boolean(string="Isolement sous le seuil", compute="_compute_isolement", store=True)

    mesure_ids = fields.One2many("jdc.mesure", "circuit_id", string="Relevés")
    mesure_count = fields.Integer(string="Relevés", compute="_compute_mesure_count")
    # Un circuit qui revient trois fois en correctif sur un an ne souffre pas
    # d'une panne mais d'une cause non traitée. C'est là que se trouve le coût caché.
    nb_correctives_12m = fields.Integer(
        string="Correctives (12 mois)",
        compute="_compute_recurrence",
        help="Nombre d'interventions correctives liées à ce circuit sur les douze derniers mois.",
    )
    recurrence_alerte = fields.Boolean(
        string="Défaillance récurrente",
        compute="_compute_recurrence",
        search="_search_recurrence_alerte",
        help="Vrai à partir de trois interventions correctives sur douze mois.",
    )
    notes = fields.Text(string="Notes")

    @api.depends("nb_feux", "nb_feux_hs", "seuil_disponibilite")
    def _compute_disponibilite(self):
        for circuit in self:
            if circuit.nb_feux <= 0:
                circuit.taux_disponibilite = 0.0
                circuit.conformite = "na"
                continue
            hs = max(0, min(circuit.nb_feux_hs, circuit.nb_feux))
            taux = (circuit.nb_feux - hs) / circuit.nb_feux * 100.0
            circuit.taux_disponibilite = taux
            if circuit.seuil_disponibilite <= 0:
                circuit.conformite = "na"
            elif hs == 0:
                circuit.conformite = "conforme"
            elif taux >= circuit.seuil_disponibilite:
                circuit.conformite = "surveillance"
            else:
                circuit.conformite = "non_conforme"

    @api.depends("isolement_mohm", "seuil_isolement")
    def _compute_isolement(self):
        for circuit in self:
            circuit.isolement_alerte = bool(
                circuit.seuil_isolement > 0
                and circuit.isolement_mohm
                and circuit.isolement_mohm < circuit.seuil_isolement
            )

    @api.depends("mesure_ids")
    def _compute_mesure_count(self):
        for circuit in self:
            circuit.mesure_count = len(circuit.mesure_ids)

    @api.depends()
    def _compute_recurrence(self):
        """Compte les correctives des douze derniers mois.

        Un circuit qui revient trois fois en correctif sur un an ne souffre pas
        d'une panne mais d'une cause non traitée. C'est là que se trouve le coût caché.
        """
        reels = self.filtered(lambda circuit: isinstance(circuit.id, int))
        for circuit in self - reels:
            circuit.nb_correctives_12m = 0
            circuit.recurrence_alerte = False
        comptes = self._compter_correctives_12m(reels)
        for circuit in reels:
            nombre = comptes.get(circuit.id, 0)
            circuit.nb_correctives_12m = nombre
            circuit.recurrence_alerte = nombre >= 3

    def _search_recurrence_alerte(self, operator, value):
        if operator not in ("=", "!="):
            return []
        comptes = self._compter_correctives_12m(self.search([]))
        alertes = [circuit_id for circuit_id, nombre in comptes.items() if nombre >= 3]
        veut_alerte = (operator == "=" and bool(value)) or (operator == "!=" and not value)
        if veut_alerte:
            return [("id", "in", alertes)]
        return [("id", "not in", alertes)]

    @api.model
    def _compter_correctives_12m(self, circuits):
        """Retourne {id circuit: nombre de correctives sur 12 mois}."""
        if not circuits:
            return {}
        limite = fields.Date.context_today(self) - relativedelta(months=12)
        interventions = self.env["jdc.intervention"].search([
            ("type_intervention", "=", "corrective"),
            ("date_intervention", ">=", limite),
            ("circuit_ids", "in", circuits.ids),
        ])
        comptes = {circuit.id: 0 for circuit in circuits}
        for intervention in interventions:
            for circuit in intervention.circuit_ids:
                if circuit.id in comptes:
                    comptes[circuit.id] += 1
        return comptes

    def write(self, vals):
        conformite_avant = {circuit.id: circuit.conformite for circuit in self}
        res = super().write(vals)
        for circuit in self:
            if conformite_avant.get(circuit.id) == "non_conforme":
                continue
            if circuit.conformite != "non_conforme":
                continue
            if circuit.activity_ids:
                continue
            libelle = circuit.designation or circuit.name
            circuit.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=fields.Date.context_today(self),
                summary="Circuit non conforme — %s" % libelle,
                note="Taux de disponibilité : %.1f %%. Seuil appliqué : %.1f %%." % (
                    circuit.taux_disponibilite,
                    circuit.seuil_disponibilite,
                ),
            )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "Nouveau":
                vals["name"] = self.env["ir.sequence"].next_by_code("jdc.circuit") or "CIR-0001"
        return super().create(vals_list)

    def action_voir_mesures(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Relevés - %s" % self.name,
            "res_model": "jdc.mesure",
            "view_mode": "tree,form",
            "domain": [("circuit_id", "=", self.id)],
            "context": {"default_circuit_id": self.id},
        }

    def action_voir_isolement(self):
        """Ouvre l'historique d'isolement du circuit, graphique en premier."""
        self.ensure_one()
        graph = self.env.ref("jdc_maintenance.view_jdc_mesure_graph")
        tree = self.env.ref("jdc_maintenance.view_jdc_mesure_tree")
        form = self.env.ref("jdc_maintenance.view_jdc_mesure_form")
        return {
            "type": "ir.actions.act_window",
            "name": "Isolement — %s" % (self.designation or self.name),
            "res_model": "jdc.mesure",
            "view_mode": "graph,tree,form",
            "views": [(graph.id, "graph"), (tree.id, "tree"), (form.id, "form")],
            "domain": [
                ("circuit_id", "=", self.id),
                ("type_controle", "=", "isolement"),
            ],
            "context": {
                "default_circuit_id": self.id,
                "default_type_controle": "isolement",
            },
        }
