# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class JdcCampagne(models.TransientModel):
    """Saisie en une fois des feux hors service et de l'isolement d'un site."""

    _name = "jdc.campagne"
    _description = "Saisie rapide de campagne"

    site_id = fields.Many2one("jdc.site", string="Site", required=True)
    date = fields.Date(string="Date de la campagne", required=True, default=fields.Date.context_today)
    ligne_ids = fields.One2many("jdc.campagne.ligne", "campagne_id", string="Circuits")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        site_id = res.get("site_id")
        if site_id and "ligne_ids" in fields_list and not res.get("ligne_ids"):
            res["ligne_ids"] = self._lignes_pour_site(site_id)
        return res

    @api.model
    def _lignes_pour_site(self, site_id):
        site = self.env["jdc.site"].browse(site_id)
        return [
            (0, 0, {
                "circuit_id": circuit.id,
                "nb_feux_hs": circuit.nb_feux_hs,
                "saisir_hs": True,
            })
            for circuit in site.circuit_ids
        ]

    @api.onchange("site_id")
    def _onchange_site_id(self):
        if not self.site_id:
            self.ligne_ids = [(5, 0, 0)]
            return
        self.ligne_ids = [(5, 0, 0)] + self._lignes_pour_site(self.site_id.id)

    def action_valider(self):
        """Crée les relevés visuels et d'isolement saisis, puis les affiche."""
        self.ensure_one()
        mesures = self.env["jdc.mesure"]
        creees = mesures.browse()
        for ligne in self.ligne_ids:
            if not ligne.circuit_id:
                continue
            if ligne.saisir_hs:
                creees |= mesures.create({
                    "circuit_id": ligne.circuit_id.id,
                    "date": self.date,
                    "type_controle": "visuel",
                    "nb_feux_hs": ligne.nb_feux_hs,
                    "conforme": ligne._conforme_feux(),
                })
            if ligne.isolement_mohm:
                creees |= mesures.create({
                    "circuit_id": ligne.circuit_id.id,
                    "date": self.date,
                    "type_controle": "isolement",
                    "isolement_mohm": ligne.isolement_mohm,
                    "conforme": ligne._conforme_isolement(),
                })
        if not creees:
            raise UserError(
                "Aucun relevé à créer. Cochez les feux à relever "
                "ou saisissez une valeur d'isolement."
            )
        return {
            "type": "ir.actions.act_window",
            "name": "Relevés créés",
            "res_model": "jdc.mesure",
            "view_mode": "tree,form",
            "domain": [("id", "in", creees.ids)],
        }


class JdcCampagneLigne(models.TransientModel):
    """Une ligne de la campagne : un circuit, ses feux hors service, son isolement."""

    _name = "jdc.campagne.ligne"
    _description = "Ligne de campagne de mesures"

    campagne_id = fields.Many2one(
        "jdc.campagne", string="Campagne", required=True, ondelete="cascade",
    )
    circuit_id = fields.Many2one("jdc.circuit", string="Circuit", required=True)
    designation = fields.Char(related="circuit_id.designation", string="Désignation")
    nb_feux = fields.Integer(related="circuit_id.nb_feux", string="Nombre de feux")
    isolement_actuel = fields.Float(
        related="circuit_id.isolement_mohm",
        string="Dernier isolement (MΩ)",
        digits=(10, 1),
    )
    saisir_hs = fields.Boolean(string="Relever les feux", default=True)
    nb_feux_hs = fields.Integer(string="Feux hors service")
    isolement_mohm = fields.Float(
        string="Nouvel isolement (MΩ)",
        digits=(10, 1),
        help="Laisser vide si l'isolement n'est pas mesuré lors de cette campagne.",
    )

    def _conforme_feux(self):
        """Vrai si le taux reste au-dessus du seuil paramétré sur le circuit."""
        circuit = self.circuit_id
        if circuit.nb_feux <= 0 or circuit.seuil_disponibilite <= 0:
            return True
        hs = max(0, min(self.nb_feux_hs, circuit.nb_feux))
        taux = (circuit.nb_feux - hs) / circuit.nb_feux * 100.0
        return taux >= circuit.seuil_disponibilite

    def _conforme_isolement(self):
        """Vrai si la valeur reste au-dessus du seuil paramétré, ou si aucun seuil n'est défini."""
        circuit = self.circuit_id
        if not circuit.seuil_isolement:
            return True
        return self.isolement_mohm >= circuit.seuil_isolement
