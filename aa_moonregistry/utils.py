import base64, json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.signing import Signer, BadSignature

from esi.openapi_clients import ESIClientProvider
from aa_moonregistry import apps
from aa_moonregistry import app_settings

from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.eveonline.models import EveCorporationInfo


from .models import SovereigntySystem

esi = ESIClientProvider(
    compatibility_date="2020-01-01",
    ua_appname=apps.DefaultConfig.verbose_name,
    ua_version=app_settings.MOON_VERSION,
    operations=[
        "GetSovereigntyMap",
        "GetCorporationsCorporationId",
        "GetAlliancesAllianceId",
    ]   
)
    
signer = Signer(salt="items-cursor")

def encode_cursor(payload: dict) -> str:
    raw = json.dumps(payload, cls=DjangoJSONEncoder, separators=(",", ":")).encode("utf-8")
    return signer.sign(base64.urlsafe_b64encode(raw).decode("ascii"))

def decode_cursor(token: str):
    try:
        signed = signer.unsign(token)
        raw = base64.urlsafe_b64decode(signed.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except BadSignature:
        return None
    

def get_sovereignty_map():
        return esi.client.Sovereignty.GetSovereigntyMap().results(use_etag=False)

def get_corporation_api_info(corporation_id):
        return esi.client.Corporation.GetCorporationsCorporationId(corporation_id=corporation_id).result(use_etag=False)

def get_alliance_api_info(alliance_id):
        return esi.client.Alliance.GetAlliancesAllianceId(alliance_id=alliance_id).result(use_etag=False)


def refresh_sovereignty():

    results = get_sovereignty_map()

    for entry in results:

        alliance_id = entry.alliance_id

        if alliance_id:

            alliance_api_result = get_alliance_api_info(alliance_id)

            eve_alliance, created = EveAllianceInfo.objects.update_or_create(
                alliance_id = alliance_id,
                defaults = {
                    'alliance_name': alliance_api_result.name,
                    'alliance_ticker': alliance_api_result.ticker,
                    'executor_corp_id': alliance_api_result.executor_corporation_id
                }            
            )

            corporation_id = entry.corporation_id

            if corporation_id:
                corp_api_result = get_corporation_api_info(corporation_id)               

                eve_corporation, created = EveCorporationInfo.objects.update_or_create(
                    corporation_id= corporation_id,
                    defaults = {
                        'corporation_name': corp_api_result.name,
                        'corporation_ticker': corp_api_result.ticker,
                        'member_count': corp_api_result.member_count,
                        'ceo_id': corp_api_result.ceo_id,
                        'alliance': eve_alliance
                    }
                )

            SovereigntySystem.objects.update_or_create(
                system_id=entry.system_id,
                defaults={
                    "alliance_id": alliance_id,
                    "corporation_id": corporation_id
                },
            )