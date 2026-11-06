# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Controles periodiques issus du guide de maintenance du balisage.
TYPES_CONTROLE = [
    ("visuel", "Inspection visuelle (mensuelle)"),
    ("isolement", "Mesure d'isolement (semestrielle)"),
    ("electrique", "Contrôle électrique (annuel)"),
    ("photometrie", "Relevé photométrique"),
]


class JdcMesure(models.Model):
    """Un relevé effectué sur un circuit lors d'un contrôle périodique."""

    _name = "jdc.mesure"
    _description = "Relevé de contrôle"
    _order = "date desc, id desc"

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau",
    )
    circuit_id = fields.Many2one("jdc.circuit", string="Circuit", required=True, ondelete="cascade")
    site_id = fields.Many2one(related="circuit_id.site_id", string="Site", store=True, readonly=True)
    systeme = fields.Selection(related="circuit_id.systeme", string="Système", store=True, readonly=True)
    intervention_id = fields.Many2one("jdc.intervention", string="Intervention", ondelete="set null")
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    type_controle = fields.Selection(TYPES_CONTROLE, string="Contrôle", required=True, default="visuel")
    operateur_id = fields.Many2one("res.users", string="Opérateur", default=lambda self: self.env.user)

    intensite_mesuree = fields.Float(string="Courant mesuré (A)", digits=(5, 2))
    isolement_mohm = fields.Float(
        string="Isolement (MΩ)",
        digits=(10, 1),
        group_operator="avg",
    )
    nb_feux_hs = fields.Integer(string="Feux hors service relevés")
    conforme = fields.Boolean(string="Conforme", default=True)
    observations = fields.Text(string="Observations")

    ecart_courant = fields.Float(
        string="Écart au nominal (A)",
        compute="_compute_ecart_courant",
        digits=(5, 2),
        help="Différence entre le courant mesuré et l'intensité nominale du circuit.",
    )

    @api.depends("intensite_mesuree", "circuit_id.intensite_nominale")
    def _compute_ecart_courant(self):
        for mesure in self:
            if mesure.intensite_mesuree and mesure.circuit_id.intensite_nominale:
                mesure.ecart_courant = mesure.intensite_mesuree - mesure.circuit_id.intensite_nominale
            else:
                mesure.ecart_courant = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "Nouveau":
                vals["name"] = self.env["ir.sequence"].next_by_code("jdc.mesure") or "MES-0001"
        mesures = super().create(vals_list)
        mesures._reporter_sur_circuit()
        return mesures

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ("isolement_mohm", "nb_feux_hs", "date", "type_controle")):
            self._reporter_sur_circuit()
        return res

    def _reporter_sur_circuit(self):
        """Met à jour le circuit avec le dernier relevé en date."""
        for mesure in self:
            circuit = mesure.circuit_id
            if not circuit:
                continue
            valeurs = {}
            if mesure.nb_feux_hs or mesure.type_controle == "visuel":
                valeurs["nb_feux_hs"] = mesure.nb_feux_hs
            if mesure.type_controle == "isolement" and mesure.isolement_mohm:
                dernier = circuit.date_isolement
                if not dernier or mesure.date >= dernier:
                    valeurs["isolement_mohm"] = mesure.isolement_mohm
                    valeurs["date_isolement"] = mesure.date
            if valeurs:
                circuit.write(valeurs)
