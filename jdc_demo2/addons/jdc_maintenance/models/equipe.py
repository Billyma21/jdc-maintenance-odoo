# -*- coding: utf-8 -*-
from odoo import api, fields, models


class JdcEquipe(models.Model):
    """Une équipe : un ou plusieurs responsables pilotent un groupe de techniciens.

    L'administrateur définit qui gère qui. Le responsable assigne ensuite les
    missions uniquement à ses techniciens. Le technicien ne crée pas
    d'intervention : il exécute celles qu'on lui assigne.
    """

    _name = "jdc.equipe"
    _description = "Équipe de maintenance"
    _order = "name"

    name = fields.Char(string="Équipe", required=True)
    active = fields.Boolean(string="Active", default=True)
    responsable_ids = fields.Many2many(
        "res.users",
        "jdc_equipe_responsable_rel",
        "equipe_id",
        "user_id",
        string="Responsables",
        domain="[('share', '=', False)]",
        help="Utilisateurs autorisés à assigner des missions aux techniciens de cette équipe.",
    )
    technicien_ids = fields.Many2many(
        "res.users",
        "jdc_equipe_technicien_rel",
        "equipe_id",
        "user_id",
        string="Techniciens",
        domain="[('share', '=', False)]",
        help="Techniciens rattachés à cette équipe. Ils ne voient que les missions qui leur sont assignées.",
    )
    notes = fields.Text(string="Notes")
    technicien_count = fields.Integer(string="Techniciens", compute="_compute_counts")
    responsable_count = fields.Integer(string="Responsables", compute="_compute_counts")
    intervention_count = fields.Integer(string="Missions", compute="_compute_counts")

    @api.depends("technicien_ids", "responsable_ids")
    def _compute_counts(self):
        Intervention = self.env["jdc.intervention"]
        for equipe in self:
            equipe.technicien_count = len(equipe.technicien_ids)
            equipe.responsable_count = len(equipe.responsable_ids)
            if equipe.technicien_ids:
                equipe.intervention_count = Intervention.search_count([
                    ("technicien_id", "in", equipe.technicien_ids.ids),
                ])
            else:
                equipe.intervention_count = 0

    @api.model_create_multi
    def create(self, vals_list):
        equipes = super().create(vals_list)
        equipes._invalidate_techniciens_geres()
        return equipes

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_techniciens_geres()
        return res

    def unlink(self):
        responsables = self.mapped("responsable_ids")
        res = super().unlink()
        if responsables:
            responsables.invalidate_recordset(["jdc_technicien_gere_ids"])
        return res

    def _invalidate_techniciens_geres(self):
        responsables = self.mapped("responsable_ids")
        if responsables:
            responsables.invalidate_recordset(["jdc_technicien_gere_ids"])

    def action_voir_interventions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Missions - %s" % self.name,
            "res_model": "jdc.intervention",
            "view_mode": "kanban,tree,form",
            "domain": [("technicien_id", "in", self.technicien_ids.ids)],
            "context": {
                "default_technicien_id": self.technicien_ids[:1].id if self.technicien_ids else False,
            },
        }
