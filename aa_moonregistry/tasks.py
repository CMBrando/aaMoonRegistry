"""Tasks."""

from celery import shared_task

from allianceauth.services.hooks import get_extension_logger
from django.core.management import call_command


from . import utils

logger = get_extension_logger(__name__)


@shared_task
def refresh_material_prices():
    call_command("aa_moonregistry_load_jita_materials_prices")

@shared_task
def refresh_metenox_data():
    call_command("aa_moonregistry_load_metenox_data")    


@shared_task
def refresh_sovereignty():
    utils.refresh_sovereignty()    
