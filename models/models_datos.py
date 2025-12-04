from odoo import models, fields, api
import logging
import requests
import os

_logger = logging.getLogger(__name__)


class AgentReceipt(models.Model):
    _name = "agent.receipt"
    _description = "Boleta / Movimiento Agente Multibanco"

    # ---------------------------
    # Datos generales
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
    # Banco / Red
    # ---------------------------
    bank = fields.Selection(
        [
            ("bcp", "BCP"),
            ("interbank", "Interbank"),
            ("bbva", "BBVA"),
            ("scotiabank", "Scotiabank"),
            ("caja_arequipa", "Caja Arequipa"),
            ("caja_cusco", "Caja Cusco"),
            ("nacion", "Banco de la Nación"),
            ("yape", "Yape"),
            ("plin", "Plin"),
            ("bim", "BIM"),
            ("kasnet", "Kasnet"),
            ("pagaya", "Pagaya"),
            ("bitel", "Bitel"),
            ("entel", "Entel"),
            ("movistar", "Movistar"),
            ("claro", "Claro"),
            ("azulito", "Azulito"),
            ("otros", "Otros"),
        ],
        string="Banco / Red",
        required=True,
    )

    # ---------------------------
    # Tipo de movimiento
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

    operator_id = fields.Many2one(
        "res.users",
        string="Operador",
        default=lambda self: self.env.user,
        readonly=True,
    )

    account = fields.Char(string="N° cuenta / N° celular")
    description = fields.Text(string="Descripción")
    cancelled = fields.Boolean(string="Anulado", default=False)

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

    # ----------------------------------------------------
    # AUTORELLENAR DNI CON API DECOLECTA
    # ----------------------------------------------------
    def _fetch_dni_decolecta(self, numero):
        """Consulta la API de Decolecta para obtener nombres."""
        token = os.getenv("DECOLECTA_TOKEN")
        if not token:
            _logger.warning("DECOLECTA_TOKEN no está configurado.")
            return {}

        url = f"https://api.decolecta.com/v1/reniec/dni?numero={numero}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            r = requests.get(url, headers=headers, timeout=12)
            data = r.json()
            raw = data.get("data", data)

            nombres = (raw.get("nombres") or "").strip()
            ap_pat = (raw.get("apellidoPaterno") or "").strip()
            ap_mat = (raw.get("apellidoMaterno") or "").strip()

            nombre_completo = f"{ap_pat} {ap_mat} {nombres}".strip()

            return {
                "nombres": nombres,
                "apellidoPaterno": ap_pat,
                "apellidoMaterno": ap_mat,
                "nombreCompleto": nombre_completo,
            }
        except Exception as e:
            _logger.error(f"Error en consulta DNI Decolecta: {e}")
        return {}

    # AUTORELLENAR solicitante
    @api.onchange("solicitante_dni")
    def _onchange_solicitante_dni(self):
        if self.solicitante_dni and len(self.solicitante_dni) == 8:
            info = self._fetch_dni_decolecta(self.solicitante_dni)
            if info:
                self.solicitante_nombre = info["nombreCompleto"]

    # AUTORELLENAR beneficiario
    @api.onchange("beneficiario_dni")
    def _onchange_beneficiario_dni(self):
        if self.beneficiario_dni and len(self.beneficiario_dni) == 8:
            info = self._fetch_dni_decolecta(self.beneficiario_dni)
            if info:
                self.beneficiario_nombre = info["nombreCompleto"]
