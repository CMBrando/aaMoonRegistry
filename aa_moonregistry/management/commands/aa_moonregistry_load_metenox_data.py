import json
import os
import tempfile
import zipfile
from collections import defaultdict
from urllib.request import urlretrieve
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Exists, OuterRef

from aa_moonregistry.models import MetenoxDrillAttribute


STANDUP_METENOX_DRILL_TYPE_ID = 82941
FUEL_NEED_ATTR = 2109

class Command(BaseCommand):
    help = 'Loads Metenox attribute data for moon drilling from SDE'

    def handle(self, *args, **kwargs):
        
        # Step 1: Get the latest build number
        self.stdout.write('Fetching latest build number from ESI...')
        latest_url = 'https://developers.eveonline.com/static-data/tranquility/latest.jsonl'

        with tempfile.TemporaryDirectory() as temp_dir:
            latest_file = os.path.join(temp_dir, 'latest.jsonl')
            urlretrieve(latest_url, latest_file)

            with open(latest_file, 'r', encoding='utf-8') as f:
                latest_data = json.loads(f.readline())
                build_number = latest_data['buildNumber']

            self.stdout.write(f'Latest build number: {build_number}')

            # Step 2: Download the static data ZIP
            zip_url = f'https://developers.eveonline.com/static-data/tranquility/eve-online-static-data-{build_number}-jsonl.zip'
            self.stdout.write(f'Downloading static data from {zip_url}...')

            zip_path = os.path.join(temp_dir, 'static-data.zip')
            urlretrieve(zip_url, zip_path)

            self.stdout.write('Extracting ZIP file...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Step 3: Load the JSONL files
            type_dogma_path = os.path.join(temp_dir, 'typeDogma.jsonl')

            if not os.path.exists(type_dogma_path):
                self.stdout.write(self.style.ERROR(
                    'Required JSONL files not found in extracted data.'
                ))
                return                  

            self.stdout.write('Loading typeDogma.jsonl...')
            fuel_value = None
            with open(type_dogma_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    
                    if item['_key'] == STANDUP_METENOX_DRILL_TYPE_ID:
                        fuel_value = next(
                            (
                                attribute["value"]
                                for attribute in item["dogmaAttributes"]
                                if attribute["attributeID"] == FUEL_NEED_ATTR
                            ),
                            None,
                        )
                        break

            self.stdout.write('Loading metenoxMoonDrill.jsonl...')
            cycleTime = None
            consumed_per_cycle = None

            
            type_metenox_path = os.path.join(temp_dir, 'metenoxMoonDrill.jsonl')

            with open(type_metenox_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    
                    cycleTime = item["miningCycleTime"]
                    consumed_per_cycle = item["reagentsConsumedPerCycle"]

            attributes = {
                "module_cycle_fuel_need": fuel_value,
                "cycle_time": cycleTime,
                "consumed_per_cycle": consumed_per_cycle,
            }

            missing_attributes = [
                name for name, value in attributes.items() if value is None
            ]
            if missing_attributes:
                raise CommandError(
                    "Missing Metenox drill attributes in SDE: "
                    + ", ".join(missing_attributes)
                )

            with transaction.atomic():
                for name, value in attributes.items():
                    MetenoxDrillAttribute.objects.update_or_create(
                        name=name,
                        defaults={"value": value},
                    )

            self.stdout.write(
                self.style.SUCCESS("Metenox drill attributes saved successfully.")
            )
