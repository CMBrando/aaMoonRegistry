# myapp/management/commands/pull_jita_orders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Avg, F, Window
from django.db.models.functions import RowNumber
from esi.openapi_clients import ESIClientProvider
from eve_sde.models import ItemType
from aa_moonregistry.models import MarketOrder, MarketPrice

from aa_moonregistry import apps
from aa_moonregistry import app_settings

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

import csv
from pathlib import Path

esi = ESIClientProvider(
    compatibility_date="2020-01-01",
    ua_appname=apps.DefaultConfig.verbose_name,
    ua_version=app_settings.MOON_VERSION,
    operations=[
        "GetMarketsRegionIdOrders"
    ]   
)

JITA_STATION_ID = 60003760
FORGE_REGION_ID = 10000002
EVE_CATEGORY_MATERIAL = 4

MAGMATIC_GAS_ID = 81143

FUEL_BLOCK_IDS = [4247, 4246, 4051, 4312]


class Command(BaseCommand):
    help = "Pulls Jita IV (Caldari Navy Assembly Plant) market orders for materials and saves them to DB"

    def handle(self, *args, **options):
        self.stdout.write("Pulling market orders for Jita IV materials...")


        save_type_ids = list(
            ItemType.objects
            .filter(group__category_id=EVE_CATEGORY_MATERIAL)
            .values_list("id", flat=True)
        )

        # Add Magmatic Gas and Fuel Blocks to the list in order to get prices for them as well
        save_type_ids.extend([MAGMATIC_GAS_ID])
        save_type_ids.extend(FUEL_BLOCK_IDS)

        run_timestamp = timezone.now()        

        all_orders = []
        page = 1
        while True:
            res = esi.client.Market.GetMarketsRegionIdOrders(
                region_id=FORGE_REGION_ID, order_type='all', page=page
            ).result(use_etag=False)

            if not res:
                break

            for order in res:
                if (
                    order.location_id == JITA_STATION_ID
                    and order.type_id in save_type_ids
                ):
                    all_orders.append(order)

            if len(res) < 1000:
                break
            page += 1

        self.stdout.write(f"Found {len(all_orders)} Jita material orders. Saving...")


        # Bulk insert/update
        objs = []
        for order in all_orders:
            objs.append(
                MarketOrder(
                    order_id=order.order_id,
                    type_id=order.type_id,
                    price=order.price,
                    volume_remain=order.volume_remain,
                    volume_total=order.volume_total,
                    min_volume=order.min_volume,
                    is_buy_order=order.is_buy_order,
                    issued=order.issued,
                    duration=order.duration,
                    location_id=order.location_id,
                    range=order.range,
                    system_id=order.system_id,
                    region_id=FORGE_REGION_ID,
                    pulled_at=run_timestamp,
                )
            )
        
        # clear existing data
        MarketOrder.objects.all().delete()

        MarketOrder.objects.bulk_create(objs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Jita material orders saved successfully."))
        

        # 1) Get BUY orders for this run, sorted by type then price DESC
        qs = (
            MarketOrder.objects
            .filter(is_buy_order=True)
            .values("type_id", "price")
            .order_by("type_id", "-price")
        )

        # 2) Average the five highest buy prices per type_id
        counts = defaultdict(int)
        sums = defaultdict(Decimal)

        for row in qs:
            t = row["type_id"]
            if counts[t] < 5:  # only the first five highest bids per type
                price = row["price"]
                # If price is float in the DB, cast to Decimal safely
                if isinstance(price, float):
                    price = Decimal(str(price))
                else:
                    price = Decimal(price)
                counts[t] += 1
                sums[t] += price

        # 3) Replace MarketPrice with the new snapshot
        MarketPrice.objects.all().delete()

        to_create = []
        for t, total in sums.items():
            avg = (total / counts[t]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            to_create.append(MarketPrice(type_id=t, price=avg))

        MarketPrice.objects.bulk_create(to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS("Saved calculated prices successfully."))
