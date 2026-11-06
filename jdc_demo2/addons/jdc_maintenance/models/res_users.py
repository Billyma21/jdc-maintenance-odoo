# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    jdc_technicien_gere_ids = fields.Many2many(
        "res.users",
        compute="_compute_jdc_techniciens_geres",
        string="Techniciens gérés",
        help="Techniciens des équipes dont cet utilisateur est responsable.",
    )

    def _compute_jdc_techniciens_geres(self):
        Equipe = self.env["jdc.equipe"].sudo()
        toutes = Equipe.search([])
        for user in self:
            user.jdc_technicien_gere_ids = toutes.filtered(
                lambda equipe: user in equipe.responsable_ids
            ).mapped("technicien_ids")
