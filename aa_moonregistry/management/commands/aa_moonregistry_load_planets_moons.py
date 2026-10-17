from django.db.models import Exists, OuterRef
from django.core.management.base import BaseCommand


from eveuniverse.models import EveSolarSystem, EvePlanet

class Command(BaseCommand):
    help = 'Loads all EveUniverse Planets and Moons for existing Systems'

    def handle(self, *args, **kwargs):
        
        enabled_sections = [
            EveSolarSystem.Section.PLANETS,
            EvePlanet.Section.MOONS,
        ]

        qs = (
            EveSolarSystem.objects
            .annotate(has_planet=Exists(
                EvePlanet.objects.filter(eve_solar_system=OuterRef("pk"))
            ))
            .filter(has_planet=False)
            .only("id")
        )

        count = qs.count()
        print(f"Found {count:,} EveSolarSystem objects missing planets to process")

        processed = 0
        for system in qs.iterator(chunk_size=500):
            EveSolarSystem.objects.get_or_create_esi(
                id=system.id,
                include_children=True,
                wait_for_children=False,
                enabled_sections=enabled_sections,
            )
            processed += 1
            if processed % 1000 == 0:
                print(f"Queued {processed:,}/{count:,} systems...")

        print(f"Queued planet + moon loads for {processed:,} solar systems.")   