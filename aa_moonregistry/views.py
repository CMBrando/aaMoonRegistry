"""Views."""

import json
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.db.models import Q, Subquery
from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse

from eve_sde.models import Constellation, ItemType, Region, SolarSystem
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from aa_moonregistry import app_settings
from .utils import decode_cursor
from .utils import encode_cursor
from .models import MoonRegistryView
from .models import MoonDetail


MOON_ORE_TYPE_IDS = (
    45490, 45491, 45492, 45493,  # R4
    45494, 45495, 45496, 45497,  # R8
    45498, 45499, 45500, 45501,  # R16
    45502, 45503, 45504, 45506,  # R32
    45510, 45511, 45512, 45513,  # R64
)
DEFAULT_EFFICIENCY = Decimal("0.90628105568")


@login_required
@permission_required("aa_moonregistry.basic_access")
def index(request):
    """Render index view."""
    context = {
        'CM_VERSION': app_settings.MOON_VERSION,
    }
    return render(request, "aa_moonregistry/index.html", context)

@login_required
@permission_required("aa_moonregistry.basic_access")
def search_universe(request):
    query = request.GET.get('query', '')
    items = list(SolarSystem.objects.filter(name__istartswith=query).values("id", "name"))
    items2 = list(Constellation.objects.filter(name__istartswith=query).values("id", "name"))
    items3 = list(Region.objects.filter(name__istartswith=query).values("id", "name"))

    merged_list = list(map(lambda x: {**x, 'name': f"{x['name']} (sys)"}, items)) + \
              list(map(lambda x: {**x, 'name': f"{x['name']} (const)"}, items2)) + \
              list(map(lambda x: {**x, 'name': f"{x['name']} (reg)"}, items3)) 

    return JsonResponse(merged_list, safe=False)


@login_required
@permission_required("aa_moonregistry.basic_access")
def search_moon_ore(request):
    query = request.GET.get("query", "").strip()
    items = list(
        ItemType.objects.filter(
            id__in=MOON_ORE_TYPE_IDS,
            name__icontains=query,
        ).order_by("name").values("id", "name")
    )

    return JsonResponse(items, safe=False)


@login_required
@permission_required("aa_moonregistry.basic_access")
def search_sov_owner(request):
    query = request.GET.get("query", "").strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    alliances = EveAllianceInfo.objects.filter(
        Q(alliance_name__icontains=query) | Q(alliance_ticker__icontains=query)
    ).order_by("alliance_name").values(
        "alliance_id", "alliance_name", "alliance_ticker"
    )[:50]
    corporations = EveCorporationInfo.objects.filter(
        Q(corporation_name__icontains=query) | Q(corporation_ticker__icontains=query)
    ).order_by("corporation_name").values(
        "corporation_id", "corporation_name", "corporation_ticker"
    )[:50]

    def label(name, ticker, kind, shorten=False):
        if shorten and len(name) > 12:
            name = f"{name[:12]}..."
        return f"{name} [{ticker}] ({kind})"

    items = [
        {
            "id": row["alliance_id"],
            "name": label(row["alliance_name"], row["alliance_ticker"], "Alliance"),
            "filter_name": label(row["alliance_name"], row["alliance_ticker"], "Alliance", shorten=True),
        }
        for row in alliances
    ] + [
        {
            "id": row["corporation_id"],
            "name": label(row["corporation_name"], row["corporation_ticker"], "Corporation"),
            "filter_name": label(row["corporation_name"], row["corporation_ticker"], "Corporation", shorten=True),
        }
        for row in corporations
    ]
    return JsonResponse(items, safe=False)


@login_required
@permission_required("aa_moonregistry.basic_access")
def get_moon_list(request):

    efficiency_param = request.GET.get("efficiency", str(DEFAULT_EFFICIENCY))
    if len(efficiency_param) > 32:
        raise SuspiciousOperation("Invalid efficiency")
    try:
        efficiency = Decimal(efficiency_param)
    except InvalidOperation as exc:
        raise SuspiciousOperation("Invalid efficiency") from exc
    if not efficiency.is_finite() or not 0 <= efficiency <= 1:
        raise SuspiciousOperation("Invalid efficiency")

    ALLOWED_SORTS = {
        "moon_name": "moon_name",
        "owner": "owner",
        "thirty_day_volume": "thirty_day_volume",
        "thirty_day_price": "thirty_day_price",
        "met_thirty_day_price": "met_thirty_day_price",
        "rarity": "rarity"
    }

    PAGE_SIZE = 2000
    ALLOWED_RARITIES = {4, 8, 16, 32, 64}

    universe_param = request.GET.get("universe", "")
    universe = universe_param.split(",") if universe_param else []
    rarity_param = request.GET.get("rarity", "")
    try:
        rarities = [int(value) for value in rarity_param.split(",") if value]
    except ValueError as exc:
        raise SuspiciousOperation("Invalid rarity") from exc
    if any(rarity not in ALLOWED_RARITIES for rarity in rarities):
        raise SuspiciousOperation("Invalid rarity")

    ore_type_id_param = request.GET.get("ore_type_id", "")
    try:
        selected_type_ids = [
            int(value) for value in ore_type_id_param.split(",") if value
        ]
    except ValueError as exc:
        raise SuspiciousOperation("Invalid moon ore type") from exc
    selected_type_ids = list(dict.fromkeys(selected_type_ids))
    if any(type_id not in MOON_ORE_TYPE_IDS for type_id in selected_type_ids):
        raise SuspiciousOperation("Invalid moon ore type")

    owner_id_param = request.GET.get("sov_owner_id", "")
    try:
        selected_owner_ids = list(dict.fromkeys(
            int(value) for value in owner_id_param.split(",") if value
        ))
    except ValueError as exc:
        raise SuspiciousOperation("Invalid sovereignty owner") from exc
    if any(owner_id <= 0 for owner_id in selected_owner_ids):
        raise SuspiciousOperation("Invalid sovereignty owner")

    sort = request.GET.get("sort", "moon_name")
    direction = request.GET.get("dir", "asc").lower()
    if sort not in ALLOWED_SORTS:
        raise SuspiciousOperation("Invalid sort")

    field = ALLOWED_SORTS[sort]
    desc = (direction == "desc")

    # Build ordering with tiebreaker matching direction
    sign = "-" if desc else ""
    ordering = [f"{sign}{field}", f"{sign}moon_id"]

    qs = MoonRegistryView.objects.order_by(*ordering)

    if universe:
        qs = qs.filter(Q(system_id__in=universe) | Q(constellation_id__in=universe) | Q(region_id__in=universe))
    if rarities:
        qs = qs.filter(rarity__in=rarities)
    if selected_owner_ids:
        qs = qs.filter(
            Q(alliance_id__in=selected_owner_ids) |
            Q(corporation_id__in=selected_owner_ids)
        )
    if selected_type_ids:
        ore_filter = Q(det_json__contains=[{"type_id": selected_type_ids[0]}])
        for type_id in selected_type_ids[1:]:
            ore_filter |= Q(det_json__contains=[{"type_id": type_id}])
        matching_moon_ids = MoonRegistryView.objects.filter(ore_filter).values(
            "moon_id"
        )
        qs = qs.filter(moon_id__in=Subquery(matching_moon_ids))

    # Cursor contains: sort, dir, last_value_for_sort, last_id
    cursor = request.GET.get("cursor")
    if cursor:
        data = decode_cursor(cursor)
        if data and data.get("sort") == sort and data.get("dir") == direction:
            last_val = data.get("last_val")
            last_id = data.get("last_id")
            
            # For ASC: next rows are (field > last_val) OR (field == last_val AND id > last_id)
            # For DESC: flip comparisons
            if last_val is None:
                # fallback: ID-only cursor paging
                if not desc:
                    qs = qs.filter(moon_id__gt=last_id)
                else:
                    qs = qs.filter(moon_id__lt=last_id)
            else:
                # normal value + tie-breaker filter
                if not desc:
                    qs = qs.filter(
                        Q(**{f"{field}__gt": last_val}) |
                        Q(**{field: last_val, "moon_id__gt": last_id})
                    )
                else:
                    qs = qs.filter(
                        Q(**{f"{field}__lt": last_val}) |
                        Q(**{field: last_val, "moon_id__lt": last_id})
                    )


    items = list(qs[:PAGE_SIZE])

    next_cursor = None
    if items:
        tail = items[-1]
        last_val = getattr(tail, field)
        # serialize datetimes/decimals to string as needed
        payload = {
            "sort": sort,
            "dir": direction,
            "last_val": last_val.isoformat() if hasattr(last_val, "isoformat") else last_val,
            "last_id": tail.moon_id,
        }
        next_cursor = encode_cursor(payload)

    return JsonResponse({
        "items": [{"moon_id": it.moon_id, "moon_name": it.moon_name, 'system_name': it.system_name, "thirty_day_volume": it.thirty_day_volume * efficiency if it.thirty_day_volume is not None else None, "thirty_day_price": it.thirty_day_price * efficiency if it.thirty_day_price is not None else None, "met_thirty_day_price": it.met_thirty_day_price, "det_json": it.det_json, "rarity": it.rarity, "alliance_id": it.alliance_id, "corporation_id": it.corporation_id, "owner": it.owner, "met_thirty_day_cost": it.met_thirty_day_cost } for it in items],
        "next_cursor": next_cursor
    })


@login_required
@require_POST
@permission_required("aa_moonregistry.basic_access")
def save_moon_detail(request):

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body.")
    if not isinstance(payload, list):
        return HttpResponseBadRequest("Expected a JSON array.")

    # Normalize + dedupe by (moon_id, type_id); keep last quantity
    keyed = {}  # {(moon_id, type_id): Decimal(quantity)}
    errors = []
    for i, item in enumerate(payload):
        try:
            moon_id = int(item["moonId"])
            type_id = int(item["oreTypeId"])
            qty = Decimal(str(item["quantity"]))
            keyed[(moon_id, type_id)] = qty
        except (KeyError, ValueError, InvalidOperation) as exc:
            errors.append({"index": i, "error": str(exc), "item": item})

    if not keyed:
        return JsonResponse({
            "processed": 0, "deleted": 0, "created": 0, "errors": errors
        }, status=400 if errors else 200)

    moon_ids = {m for (m, _t) in keyed.keys()}
    new_rows = [
        MoonDetail(moon_id=m, type_id=t, quantity=q)
        for (m, t), q in keyed.items()
    ]

    with transaction.atomic():
        deleted_count, _ = MoonDetail.objects.filter(moon_id__in=moon_ids).delete()
        MoonDetail.objects.bulk_create(new_rows)

    return JsonResponse({
        "success": (len(errors) == 0),
        "processed": len(moon_ids),
        "errors": errors,
    })
