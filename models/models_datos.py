from odoo import models, fields, api


class AgentReceipt(models.Model):
    _name = "agent.receipt"
    _description = "Boleta / Movimiento Agente Multibanco"

    # ---------------------------
    # Datos generales de la boleta
    # ---------------------------
    name = fields.Char(
        string="N° Boleta",
        readonly=True,
        copy=False,
        default="Nuevo",
    )

    date = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
    )

    # ---------------------------
    # Banco / Red (Selection => lista desplegable)
    # ---------------------------
    bank = fields.Selection(
        [
            ("bcp", "BCP"),
            ("interbank", "INTERBANK"),
            ("bbva", "BBVA"),
            ("scotiabank", "SCOTIABANK"),
            ("caja_arequipa", "CAJA AREQUIPA"),
            ("caja_cusco", "CAJA CUSCO"),
            ("banco_nacion", "BANCO DE LA NACION"),
            ("yape", "YAPE"),
            ("plin", "PLIN"),
            ("bim", "BIM"),
            ("kasnet", "KASNET"),
            ("pagaya", "PAGAYA"),
            ("bitel", "BITEL"),
            ("entel", "ENTEL"),
            ("movistar", "MOVISTAR"),
            ("claro", "CLARO"),
            ("azulito", "AZULITO"),
            ("otros", "Otros"),
        ],
        string="Banco / Red",
        required=True,
    )

    # ---------------------------
    # Tipo de movimiento (Selection => lista desplegable)
    # ---------------------------
    movement = fields.Selection(
        [
            ("deposit", "Depósito"),
            ("withdrawal", "Retiro"),
            ("giro", "Giro"),
            ("payment", "Pago"),
            ("recharge", "Recarga"),
            ("other", "Otros"),
        ],
        string="Tipo de movimiento",
        required=True,
    )

    # ---------------------------
    # Operador
    # ---------------------------
    operator_id = fields.Many2one(
        "res.users",
        string="Operador",
        default=lambda self: self.env.user,
        readonly=True,
    )

    # ---------------------------
    # Otros datos generales
    # ---------------------------
    account = fields.Char(string="N° cuenta / N° celular")
    description = fields.Text(string="Descripción")
    cancelled = fields.Boolean(string="Anulado")

    # ---------------------------
    # Datos del solicitante
    # ---------------------------
    solicitante_dni = fields.Char(string="DNI solicitante")
    solicitante_nombre = fields.Char(string="Nombre solicitante")

    # ---------------------------
    # Datos del beneficiario
    # ---------------------------
    beneficiario_dni = fields.Char(string="DNI beneficiario")
    beneficiario_nombre = fields.Char(string="Nombre beneficiario")

    # ---------------------------
    # Montos
    # ---------------------------
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id.id,
    )

    amount = fields.Monetary(
        string="Monto",
        currency_field="currency_id",
    )

    fee = fields.Monetary(
        string="Comisión",
        currency_field="currency_id",
    )

    total = fields.Monetary(
        string="Total",
        currency_field="currency_id",
        compute="_compute_total",
        store=True,
        readonly=True,
    )

    @api.depends("amount", "fee")
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.amount or 0.0) + (rec.fee or 0.0)
