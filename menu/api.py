from datetime import datetime
from decimal import Decimal
import io

from django.contrib.auth import get_user_model
from django.db.models import (
    Q, F, Sum, Count, Value as V, DecimalField, ExpressionWrapper, Avg, Max, Min
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from docx import Document

from .models import Customer, Order, OrderItem, Menu as MenuItem
from .serializers import CustomerSerializer, OrderSerializer, OrderItemSerializer
from .permissions import IsAdminOrReadOnly

User = get_user_model()



def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _iter_order_items(order):
    for attr in ("items", "order_items", "orderitem_set"):
        if hasattr(order, attr):
            qs = getattr(order, attr)
            try:
                return qs.all()
            except Exception:
                return qs
    return []


def _get_item_title(item):
    for attr in ("title", "name", "label", "product_name"):
        if hasattr(item, attr):
            val = getattr(item, attr)
            if callable(val):
                try:
                    return val()
                except Exception:
                    continue
            return val
    for rel in ("menu", "menu_item", "item", "product", "dish"):
        if hasattr(item, rel):
            obj = getattr(item, rel)
            for attr in ("title", "name", "label"):
                if hasattr(obj, attr):
                    return getattr(obj, attr)
    return "—"


def _get_unit_price(item) -> Decimal:
    for attr in ("unit_price", "price", "cost"):
        if hasattr(item, attr):
            try:
                return Decimal(getattr(item, attr) or 0)
            except Exception:
                pass
    if hasattr(item, "menu") and getattr(item, "menu") is not None:
        try:
            return Decimal(getattr(item.menu, "price", 0) or 0)
        except Exception:
            return Decimal("0")
    return Decimal("0")


def _get_customer_name(order):
    c = getattr(order, "customer", None)
    if not c:
        return "—"
    for attr in ("full_name", "fio", "name"):
        if hasattr(c, attr):
            return getattr(c, attr)
    first = getattr(c, "first_name", "")
    last = getattr(c, "last_name", "")
    mid = getattr(c, "middle_name", "")
    t = " ".join(x for x in (last, first, mid) if x)
    return t or "—"


STATUS_LABELS = {
    "NEW": "Новый",
    "IN_PROGRESS": "Готовится",
    "DONE": "Готов",
    "PAID": "Оплачен",
    "CANCELLED": "Отменён",
    "new": "Новый",
    "in_progress": "Готовится",
    "done": "Готов",
    "paid": "Оплачен",
    "canceled": "Отменён",
}




class BaseExportMixin:
    ROW_LIMIT = 50000

    def _excel_autowidth(self, ws):
        for column_cells in ws.columns:
            length = 0
            col = column_cells[0].column if hasattr(column_cells[0], "column") else 1
            for cell in column_cells:
                try:
                    length = max(length, len(str(cell.value)))
                except Exception:
                    pass
            ws.column_dimensions[get_column_letter(col)].width = min(length + 2, 60)

    def _make_excel(self, sheets):
        wb = Workbook()
        ws = wb.active
        if sheets:
            title, headers, rows = sheets[0]
            ws.title = title[:31] or "Sheet1"
            if headers:
                ws.append(headers)
            for r in rows[: self.ROW_LIMIT]:
                ws.append(r)
            self._excel_autowidth(ws)

        for title, headers, rows in sheets[1:]:
            ws = wb.create_sheet(title=title[:31] or "Sheet")
            if headers:
                ws.append(headers)
            for r in rows[: self.ROW_LIMIT]:
                ws.append(r)
            self._excel_autowidth(ws)

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    def _make_word(self, title, blocks):
        doc = Document()
        doc.add_heading(title, 0)
        for blk in blocks:
            if blk.get("type") == "text":
                doc.add_paragraph(blk.get("text", ""))
            elif blk.get("type") == "table":
                headers = blk.get("headers") or []
                rows = blk.get("rows") or []
                table = doc.add_table(rows=1, cols=len(headers))
                hdr = table.rows[0].cells
                for i, h in enumerate(headers):
                    hdr[i].text = str(h)
                for row in rows[: self.ROW_LIMIT]:
                    cells = table.add_row().cells
                    for j, val in enumerate(row):
                        cells[j].text = "" if val is None else str(val)
        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        return stream

    def _download(self, stream, filename, content_type):
        resp = HttpResponse(stream, content_type=content_type)
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


# ------------------------------ Orders ------------------------------

class OrdersViewSet(viewsets.ModelViewSet, BaseExportMixin):
    """
    USER: только чтение; ADMIN: полный CRUD.
    Массовый экспорт — только ADMIN.
    """
    queryset = Order.objects.all().select_related("customer")
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()

        # фильтры из query params
        p = self.request.query_params
        date_from = _parse_date(p.get("date_from"))
        date_to = _parse_date(p.get("date_to"))
        status = p.get("status")
        customer_id = p.get("customer_id")
        search = p.get("search")
        sort = p.get("sort")

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if status:
            qs = qs.filter(status=status)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        if search:
            cond = Q(id__icontains=search)
            cond |= Q(customer__name__icontains=search) | Q(customer__fio__icontains=search) | Q(customer__full_name__icontains=search)
            qs = qs.filter(cond)

        qs = qs.order_by(sort) if sort else qs.order_by("-id")

        money = ExpressionWrapper(
            F("items__qty") * F("items__menu__price"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        qs = qs.annotate(
            items_count=Coalesce(Count("items"), V(0)),
            total_amount=Coalesce(
                Sum(money),
                V(0, output_field=DecimalField(max_digits=14, decimal_places=2)),
            ),
        )
        return qs

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(
            count=Count("id"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def export(self, request):
        qs = self.get_queryset()

        file_type = (request.query_params.get("type") or "excel").lower()
        include_items = (request.query_params.get("include_items") or "false").lower() == "true"
        include_summary = (request.query_params.get("include_summary") or "true").lower() != "false"

        orders_headers = ["ID", "Клиент", "Статус", "Создан", "Позиций", "Сумма, ₽"]
        orders_rows = []
        for o in qs:
            created = getattr(o, "created_at", None)
            created_str = created.strftime("%Y-%m-%d %H:%M") if created else ""
            items_count = getattr(o, "items_count", None)
            total_amount = getattr(o, "total_amount", None)
            if items_count is None or total_amount is None:
                its = list(_iter_order_items(o))
                items_count = len(its)
                total_amount = sum(Decimal(getattr(i, "qty", 0)) * _get_unit_price(i) for i in its)

            orders_rows.append([
                o.id,
                _get_customer_name(o),
                STATUS_LABELS.get(getattr(o, "status", ""), getattr(o, "status", "") or "—"),
                created_str,
                int(items_count),
                f"{Decimal(total_amount):.2f}",
            ])

        items_headers = ["ID", "OrderID", "Блюдо", "Кол-во", "Цена, ₽", "Итого, ₽"]
        items_rows = []
        if include_items:
            qs = qs.prefetch_related("items", "items__menu")
            for o in qs:
                for it in _iter_order_items(o):
                    qty = getattr(it, "qty", 0) or 0
                    up = _get_unit_price(it)
                    items_rows.append([
                        getattr(it, "id", None),
                        o.id,
                        _get_item_title(it),
                        qty,
                        f"{up:.2f}",
                        f"{(Decimal(qty) * up):.2f}",
                    ])

        summary_headers = ["Показатель", "Значение"]
        summary_rows = []
        if include_summary:
            cnt = len(orders_rows)
            total = sum(Decimal(r[5].replace(",", ".").replace(" ", "")) for r in orders_rows) if orders_rows else Decimal("0")
            avg = total / cnt if cnt else Decimal("0")
            summary_rows.extend([
                ["Количество заказов", cnt],
                ["Суммарная выручка, ₽", f"{total:.2f}"],
                ["Средний чек, ₽", f"{avg:.2f}"],
            ])

        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        fname = f"orders_{now}"

        if file_type == "word":
            blocks = [
                {"type": "text", "text": "Экспорт заказов (с учётом фильтров)"},
                {"type": "table", "headers": orders_headers, "rows": orders_rows},
            ]
            if include_items:
                blocks.append({"type": "table", "headers": items_headers, "rows": items_rows})
            if include_summary:
                blocks.append({"type": "table", "headers": summary_headers, "rows": summary_rows})
            stream = self._make_word("Orders Export", blocks)
            return self._download(
                stream,
                f"{fname}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        sheets = [("Orders", orders_headers, orders_rows)]
        if include_items:
            sheets.append(("OrderItems", items_headers, items_rows))
        if include_summary:
            sheets.append(("Summary", summary_headers, summary_rows))
        stream = self._make_excel(sheets)
        return self._download(
            stream,
            f"{fname}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )




class OrderItemsViewSet(viewsets.ModelViewSet, BaseExportMixin):
    """
    USER: только чтение; ADMIN: полный CRUD.
    Экспорт — только ADMIN.
    """
    queryset = OrderItem.objects.all().select_related("order", "menu")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        order_id = p.get("order_id")
        date_from = _parse_date(p.get("date_from"))
        date_to = _parse_date(p.get("date_to"))
        search = p.get("search")
        sort = p.get("sort")

        if order_id:
            qs = qs.filter(order_id=order_id)
        if date_from:
            qs = qs.filter(order__created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(order__created_at__date__lte=date_to)

        if search:
            cond = Q(id__icontains=search) | Q(order__id__icontains=search)
            qs = qs.filter(cond)

        qs = qs.order_by(sort) if sort else qs.order_by("-id")

        qs = qs.annotate(
            line_total=ExpressionWrapper(
                F("qty") * F("menu__price"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        return qs

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        data = qs.aggregate(
            count=Count("id"),
            avg=Avg("id"),
            max=Max("id"),
            min=Min("id"),
        )
        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def export(self, request):
        qs = self.get_queryset()
        file_type = (request.query_params.get("type") or "excel").lower()

        headers = ["ID", "OrderID", "Блюдо", "Кол-во", "Цена, ₽", "Итого, ₽"]
        rows = []
        for it in qs:
            qty = getattr(it, "qty", 0) or 0
            up = _get_unit_price(it)
            line = getattr(it, "line_total", None)
            if line is None:
                line = Decimal(qty) * up
            rows.append([
                getattr(it, "id", None),
                getattr(it, "order_id", None),
                _get_item_title(it),
                qty,
                f"{up:.2f}",
                f"{Decimal(line):.2f}",
            ])

        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        fname = f"order_items_{now}"

        if file_type == "word":
            stream = self._make_word("Order Items Export", [
                {"type": "table", "headers": headers, "rows": rows}
            ])
            return self._download(
                stream,
                f"{fname}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        stream = self._make_excel([("OrderItems", headers, rows)])
        return self._download(
            stream,
            f"{fname}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
