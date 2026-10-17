"""Models."""

from django.db import models
from eveuniverse.models import EveType
from django.utils import timezone



class General(models.Model):
    """A meta model for app permissions."""

    class Meta:  # pylint: disable=too-few-public-methods
        """
        aa_moonregistry :: Meta
        """
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", ("Can view moon registry")),
        )

        verbose_name = ("aa_moonregistry")


class SovereigntySystem(models.Model):
    system_id = models.IntegerField(primary_key=True)
    alliance_id = models.IntegerField()
    corporation_id = models.IntegerField(null=True)

    class Meta:
        default_permissions = ()

class MarketOrder(models.Model):
    order_id = models.BigIntegerField(primary_key=True)
    type     = models.ForeignKey(EveType, on_delete=models.CASCADE)
    price = models.FloatField()
    volume_remain = models.IntegerField()
    volume_total = models.IntegerField()
    min_volume = models.IntegerField()
    is_buy_order = models.BooleanField()
    issued = models.DateTimeField()
    duration = models.IntegerField()
    location_id = models.IntegerField()
    range = models.CharField(max_length=50)
    system_id = models.IntegerField()
    region_id = models.IntegerField()
    pulled_at = models.DateTimeField(default=timezone.now)        

    class Meta:
        default_permissions = ()        


class MarketPrice(models.Model):
    type = models.OneToOneField(EveType, on_delete=models.CASCADE, primary_key=True)
    price = models.DecimalField(max_digits=20, decimal_places=2)


class MoonDetail(models.Model):
    id = models.AutoField(primary_key=True) 
    moon_id = models.IntegerField(db_index=True)    
    type_id = models.IntegerField()
    quantity = models.DecimalField(max_digits=18, decimal_places=12)

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields=["moon_id", "type_id"], name="uniq_moon_type")
        ]       


class MetenoxDrillAttribute(models.Model):
    name = models.CharField(max_length=25, primary_key=True)
    value = models.DecimalField(max_digits=20, decimal_places=5)

    class Meta:
        default_permissions = ()     

   

class MoonRegistryView(models.Model):
    region_id = models.IntegerField(blank=False, null=False)
    constellation_id = models.IntegerField(blank=False, null=False)
    system_id = models.IntegerField(blank=False, null=False)
    system_name = models.CharField(blank=True, max_length=100) 
    planet_id = models.IntegerField(blank=False, null=False)
    moon_id = models.IntegerField(primary_key=True, blank=False, null=False)
    moon_name = models.CharField(blank=True, max_length=250)
    alliance_id = models.IntegerField(blank=True, null=True)
    corporation_id = models.IntegerField(blank=True, null=True)
    owner = models.CharField(blank=True, max_length=250)
    rarity = models.IntegerField(blank=True, null=True)
    thirty_day_volume = models.DecimalField(max_digits=18, decimal_places=12)
    thirty_day_price = models.DecimalField(max_digits=20, decimal_places=12)
    met_thirty_day_price = models.DecimalField(max_digits=20, decimal_places=12)
    met_thirty_day_cost = models.DecimalField(max_digits=20, decimal_places=12)   
    det_json = models.JSONField(default=list, null=True)

    class Meta:
        managed = False              
        default_permissions = ()        
        db_table = "aa_moonregistry_view"    
