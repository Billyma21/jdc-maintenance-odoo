# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class JdcIntervention(models.Model):
    """Une intervention realisee sur un site, preventive ou corrective.

    Le responsable crée et assigne la mission. Le technicien la reçoit, la
    complète, imprime le bon, joint la photo signée, puis attend la suivante.
    """

    _name = "jdc.intervention"
    _description = "Intervention"
    _inherit = ["mail.thread"]
    _order = "date_intervention desc, id desc"

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau",
    )
    site_id = fields.Many2one("jdc.site", string="Site", required=True, ondelete="restrict", tracking=True)
    contrat_id = fields.Many2one(
        "jdc.contrat",
        string="Contrat",
        domain="[('site_id', '=', site_id)]",
        ondelete="set null",
    )
    partner_id = fields.Many2one(related="site_id.partner_id", string="Client", store=True, readonly=True)
    date_intervention = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    type_intervention = fields.Selection(
        selection=[
            ("preventive", "Préventive"),
            ("corrective", "Corrective"),
        ],
        string="Type",
        default="preventive",
        required=True,
        tracking=True,
    )
    technicien_id = fields.Many2one(
        "res.users",
        string="Technicien assigné",
        tracking=True,
        domain=lambda self: self._domain_techniciens_assignables(),
        help="Seul un responsable peut assigner un technicien de son équipe.",
    )
    equipe_id = fields.Many2one(
        "jdc.equipe",
        string="Équipe",
        compute="_compute_equipe_id",
        store=True,
        help="Équipe déduite du technicien assigné.",
    )
    duree = fields.Float(string="Durée (h)", help="Temps passé sur site, en heures.")
    travail_de_nuit = fields.Boolean(
        string="Intervention de nuit",
        help="Les travaux sur piste se font souvent hors trafic.",
    )
    etat = fields.Selection(
        selection=[
            ("planifie", "Planifiée"),
            ("en_cours", "En cours"),
            ("termine", "Terminée"),
            ("annule", "Annulée"),
        ],
        string="État",
        default="planifie",
        required=True,
        tracking=True,
    )
    nature = fields.Selection(
        selection=[
            ("visite", "Visite périodique"),
            ("depannage", "Dépannage"),
            ("mesure", "Campagne de mesures"),
            ("mise_en_service", "Mise en service"),
            ("travaux", "Travaux neufs"),
        ],
        string="Nature",
        default="visite",
        required=True,
    )
    circuit_ids = fields.Many2many(
        "jdc.circuit",
        string="Circuits concernés",
        domain="[('site_id', '=', site_id)]",
    )
    mesure_ids = fields.One2many("jdc.mesure", "intervention_id", string="Relevés")
    mesure_count = fields.Integer(string="Relevés", compute="_compute_mesure_count")
    habilitation = fields.Char(
        string="Habilitation électrique",
        help="Habilitation requise au titre de la NF C18-510, par exemple B2V ou BR.",
    )
    consignation = fields.Boolean(
        string="Consignation du circuit",
        help="Le circuit a été consigné avant intervention.",
    )
    description = fields.Text(string="Travaux réalisés")
    constat = fields.Text(string="Constat et anomalies")
    suite_a_donner = fields.Text(string="Suite à donner")
    signataire = fields.Char(string="Visa client", help="Nom du représentant du client sur site.")

    bon_signe = fields.Binary(
        string="Photo du bon signé",
        attachment=True,
        help="Photo ou scan du bon d'intervention signé par le client. "
             "C'est cette pièce qui confirme le visa sur place.",
    )
    bon_signe_filename = fields.Char(string="Nom du fichier")
    bon_confirme = fields.Boolean(
        string="Bon confirmé",
        compute="_compute_bon_confirme",
        store=True,
        help="Vrai dès qu'une photo ou un scan du bon signé est joint.",
    )
    date_bon_confirme = fields.Datetime(
        string="Confirmé le",
        readonly=True,
        copy=False,
    )

    @api.model
    def _domain_techniciens_assignables(self):
        """Limite la liste des techniciens selon le profil connecté."""
        user = self.env.user
        tech_group = self.env.ref("jdc_maintenance.group_jdc_technicien")
        base_domain = [("share", "=", False), ("groups_id", "in", tech_group.id)]
        if user.has_group("jdc_maintenance.group_jdc_admin") or user.has_group("base.group_system"):
            return base_domain
        if user.has_group("jdc_maintenance.group_jdc_manager"):
            ids = user.jdc_technicien_gere_ids.ids
            return [("id", "in", ids)] if ids else [("id", "=", 0)]
        return [("id", "=", user.id)]

    @api.depends("technicien_id")
    def _compute_equipe_id(self):
        Equipe = self.env["jdc.equipe"]
        for intervention in self:
            if not intervention.technicien_id:
                intervention.equipe_id = False
                continue
            equipe = Equipe.search([
                ("technicien_ids", "in", intervention.technicien_id.id),
            ], limit=1)
            intervention.equipe_id = equipe

    @api.depends("mesure_ids")
    def _compute_mesure_count(self):
        for intervention in self:
            intervention.mesure_count = len(intervention.mesure_ids)

    @api.depends("bon_signe")
    def _compute_bon_confirme(self):
        for intervention in self:
            intervention.bon_confirme = bool(intervention.bon_signe)

    @api.onchange("site_id")
    def _onchange_site_id(self):
        """Vide le contrat et les circuits s'ils n'appartiennent plus au site choisi."""
        if self.contrat_id and self.contrat_id.site_id != self.site_id:
            self.contrat_id = False
        if self.circuit_ids:
            self.circuit_ids = self.circuit_ids.filtered(lambda c: c.site_id == self.site_id)

    def _jdc_est_responsable_ou_admin(self):
        return (
            self.env.user.has_group("jdc_maintenance.group_jdc_manager")
            or self.env.user.has_group("jdc_maintenance.group_jdc_admin")
            or self.env.user.has_group("base.group_system")
        )

    def _jdc_partenaires_suivi(self):
        """Technicien assigné + responsables de son équipe + créateur."""
        self.ensure_one()
        partners = self.env["res.partner"]
        if self.technicien_id.partner_id:
            partners |= self.technicien_id.partner_id
        if self.technicien_id:
            equipes = self.env["jdc.equipe"].sudo().search([
                ("technicien_ids", "in", self.technicien_id.id),
            ])
            partners |= equipes.responsable_ids.mapped("partner_id")
        if self.create_uid.partner_id:
            partners |= self.create_uid.partner_id
        # Tous les responsables de l'équipe liée, si connue
        if self.equipe_id:
            partners |= self.equipe_id.responsable_ids.mapped("partner_id")
        return partners

    def _jdc_abonner_suivi(self):
        """Abonne technicien et responsables pour qu'ils reçoivent les messages."""
        for intervention in self:
            partners = intervention._jdc_partenaires_suivi()
            partner_ids = partners.ids
            if partner_ids:
                intervention.message_subscribe(partner_ids=partner_ids)

    def _jdc_verifier_assignation(self, technicien):
        """Empêche d'assigner un technicien hors de son périmètre."""
        if not technicien:
            return
        user = self.env.user
        if user.has_group("jdc_maintenance.group_jdc_admin") or user.has_group("base.group_system"):
            return
        if not user.has_group("jdc_maintenance.group_jdc_manager"):
            raise AccessError("Seul un responsable peut assigner un technicien à une mission.")
        if technicien not in user.jdc_technicien_gere_ids:
            raise UserError(
                "Le technicien « %s » ne fait pas partie de vos équipes. "
                "Demandez à l'administrateur de l'ajouter à une équipe que vous gérez."
                % technicien.display_name
            )

    @api.model_create_multi
    def create(self, vals_list):
        if not self._jdc_est_responsable_ou_admin():
            raise AccessError(
                "Un technicien ne peut pas créer d'intervention. "
                "Attendez qu'un responsable vous assigne une mission."
            )
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "Nouveau":
                vals["name"] = self.env["ir.sequence"].next_by_code("jdc.intervention") or "INT-0001"
            if vals.get("bon_signe") and not vals.get("date_bon_confirme"):
                vals["date_bon_confirme"] = fields.Datetime.now()
            if vals.get("technicien_id"):
                self._jdc_verifier_assignation(self.env["res.users"].browse(vals["technicien_id"]))
        interventions = super().create(vals_list)
        interventions._jdc_abonner_suivi()
        for intervention in interventions.filtered("technicien_id"):
            intervention.message_post(
                body="Mission assignée à %s." % intervention.technicien_id.display_name,
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )
        return interventions

    def write(self, vals):
        if "technicien_id" in vals and not self._jdc_est_responsable_ou_admin():
            raise AccessError("Seul un responsable peut (ré)assigner un technicien.")
        if vals.get("technicien_id"):
            self._jdc_verifier_assignation(self.env["res.users"].browse(vals["technicien_id"]))
        if "bon_signe" in vals:
            if vals.get("bon_signe"):
                vals.setdefault("date_bon_confirme", fields.Datetime.now())
            else:
                vals["date_bon_confirme"] = False
        res = super().write(vals)
        if "technicien_id" in vals:
            self._jdc_abonner_suivi()
            for intervention in self:
                if intervention.technicien_id:
                    intervention.message_post(
                        body="Mission assignée à %s." % intervention.technicien_id.display_name,
                        message_type="notification",
                        subtype_xmlid="mail.mt_note",
                    )
        if vals.get("bon_signe"):
            self._jdc_abonner_suivi()
            for intervention in self:
                intervention.message_post(
                    body="Bon d'intervention signé enregistré. Visa client confirmé par photo.",
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )
        return res

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        """Garantit l'abonnement et la notification des responsables."""
        self._jdc_abonner_suivi()
        # Un message « discussion » notifie les abonnés (responsable inclus).
        if not kwargs.get("subtype_xmlid") and kwargs.get("message_type") == "comment":
            kwargs.setdefault("subtype_xmlid", "mail.mt_comment")
        # Destinataires forcés : technicien + responsables d'équipe (hors auteur).
        if kwargs.get("subtype_xmlid") == "mail.mt_comment" or kwargs.get("message_type") == "comment":
            destinataires = self.env["res.partner"]
            for intervention in self:
                destinataires |= intervention._jdc_partenaires_suivi()
            destinataires -= self.env.user.partner_id
            existants = set(kwargs.get("partner_ids") or [])
            kwargs["partner_ids"] = list(existants | set(destinataires.ids))
        return super().message_post(**kwargs)

    def action_demarrer(self):
        self.write({"etat": "en_cours"})

    def action_terminer(self):
        self.write({"etat": "termine"})
        self._jdc_abonner_suivi()
        for intervention in self:
            intervention.message_post(
                body="Intervention terminée par %s." % self.env.user.display_name,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

    def action_annuler(self):
        self.write({"etat": "annule"})

    def action_remettre_brouillon(self):
        if not self._jdc_est_responsable_ou_admin():
            raise AccessError("Seul un responsable peut replanifier une mission.")
        self.write({"etat": "planifie"})

    def action_imprimer_bon(self):
        """Ouvre le PDF du bon d'intervention, prêt à être signé sur place."""
        self.ensure_one()
        return self.env.ref("jdc_maintenance.action_report_jdc_intervention").report_action(self)

    def action_confirmer_bon(self):
        """Enregistre la confirmation une fois la photo du bon signé jointe."""
        self.ensure_one()
        if not self.bon_signe:
            raise UserError(
                "Joignez d'abord la photo ou le scan du bon signé par le client, "
                "puis confirmez."
            )
        self.write({"date_bon_confirme": fields.Datetime.now()})
        self.message_post(
            body="Bon d'intervention confirmé.",
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        return True
