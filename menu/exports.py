from datetime import datetime
from decimal import Decimal
import io

from django.db.models import Q, F, Sum, Count, Value as V
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from docx import Document

from .models import Order


STATUS_LABELS = {
    "NEW": "Новый",
    "IN_PROGRESS": "Готовится",
    "DONE": "Готов",
    "PAID": "Оплачен",
    "CANCELLED": "Отменён",
    "CANCELED": "Отменён",
    "CANCEL": "Отменён",
}

def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def _iter_order_items(order):
    for rel in ("items", "order_items", "orderitem_set"):
        if hasattr(order, rel):
            qs = getattr(order, rel)
            try:
                return qs.all()
            except Exception:
                return qs
    return []

def _get_customer_name(order):
    c = getattr(order, "customer", None)
    if not c:
        return "—"
    for a in ("name", "full_name", "fio"):
        if hasattr(c, a):
            return getattr(c, a)
    first = getattr(c, "first_name", "")
    last = getattr(c, "last_name", "")
    mid = getattr(c, "middle_name", "")
    t = " ".join(x for x in (last, first, mid) if x)
    return t or str(getattr(c, "id", "—"))

def _get_unit_price(item):
    for a in ("unit_price", "price", "cost"):
        if hasattr(item, a):
            v = getattr(item, a)
            return Decimal(v or 0)
    if hasattr(item, "menu") and getattr(item, "menu") is not None:
        return Decimal(getattr(item.menu, "price", 0) or 0)
    return Decimal("0")

def _get_title(item):
    if hasattr(item, "menu"):
        obj = getattr(item, "menu")
        for a in ("title", "name"):
            if hasattr(obj, a):
                return getattr(obj, a)
    for a in ("title", "name", "label"):
        if hasattr(item, a):
            return getattr(item, a)
    return f"Позиция #{getattr(item, 'id', '') or '—'}"

def _excel_autowidth(ws):
    for col in ws.columns:
        length = 0
        idx = col[0].column if hasattr(col[0], "column") else 1
        for cell in col:
            try:
                length = max(length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[get_column_letter(idx)].width = min(length + 2, 60)

def _make_excel(sheets, row_limit=50000):
    wb = Workbook()
    title, headers, rows = sheets[0]
    ws = wb.active
    ws.title = title[:31] or "Sheet1"
    if headers:
        ws.append(headers)
    for r in rows[:row_limit]:
        ws.append(r)
    _excel_autowidth(ws)

    for title, headers, rows in sheets[1:]:
        ws = wb.create_sheet(title=title[:31] or "Sheet")
        if headers:
            ws.append(headers)
        for r in rows[:row_limit]:
            ws.append(r)
        _excel_autowidth(ws)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream

def _make_word(title, blocks, row_limit=50000):
    doc = Document()
    doc.add_heading(title, 0)
    for blk in blocks:
        t = blk.get("type")
        if t == "text":
            doc.add_paragraph(blk.get("text", ""))
        elif t == "table":
            headers = blk.get("headers") or []
            rows = blk.get("rows") or []
            table = doc.add_table(rows=1, cols=len(headers))
            hdr = table.rows[0].cells
            for i, h in enumerate(headers):
                hdr[i].text = str(h)
            for r in rows[:row_limit]:
                cells = table.add_row().cells
                for j, v in enumerate(r):
                    cells[j].text = "" if v is None else str(v)
    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)
    return stream


class OrdersExportView(APIView):
    """
    Массовый экспорт заказов: только для ADMIN.
    """
    permission_classes = [IsAdminUser]
    ROW_LIMIT = 50000

    def get(self, request, *args, **kwargs):
        
       
        from django.db.models import Sum

        qs = Order.objects.all().select_related("customer").order_by("-id")

        orders_headers = ["ID", "Клиент", "Статус", "Создан", "Позиций", "Сумма, ₽"]
        orders_rows = []
        for o in qs:
            created = getattr(o, "created_at", None)
            created_str = created.strftime("%Y-%m-%d %H:%M") if created else ""
            its = list(_iter_order_items(o))
            total = sum(Decimal(getattr(i, "qty", 0)) * _get_unit_price(i) for i in its)
            orders_rows.append([
                o.id,
                _get_customer_name(o),
                STATUS_LABELS.get(getattr(o, "status", ""), getattr(o, "status", "") or "—"),
                created_str,
                len(its),
                f"{total:.2f}",
            ])

        file_type = (request.query_params.get("type") or "excel").lower()
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        fname = f"orders_{now}"

        if file_type == "word":
            blocks = [
                {"type": "text", "text": "Экспорт заказов"},
                {"type": "table", "headers": orders_headers, "rows": orders_rows},
            ]
            stream = _make_word("Orders Export", blocks, row_limit=self.ROW_LIMIT)
            resp = HttpResponse(
                stream,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            resp["Content-Disposition"] = f'attachment; filename="{fname}.docx"'
            return resp

        stream = _make_excel([("Orders", orders_headers, orders_rows)], row_limit=self.ROW_LIMIT)
        resp = HttpResponse(
            stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{fname}.xlsx"'
        return resp
