# Replacement for the original eveuniverse-based migrations on fresh installs.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    replaces = [
        ("aa_moonregistry", "0001_initial"),
        ("aa_moonregistry", "0002_create_moonregistry_view"),
    ]
    dependencies = [
        ("eve_sde", "0036_remove_star_name"),
        ("eveonline", "0019_v5squash"),
    ]
    operations = [
        migrations.CreateModel(
            name='General',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'aa_moonregistry',
                'permissions': (('basic_access', 'Can view moon registry'),),
                'managed': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='MoonRegistryView',
            fields=[
                ('region_id', models.IntegerField()),
                ('constellation_id', models.IntegerField()),
                ('system_id', models.IntegerField()),
                ('system_name', models.CharField(blank=True, max_length=100)),
                ('planet_id', models.IntegerField()),
                ('moon_id', models.IntegerField(primary_key=True, serialize=False)),
                ('moon_name', models.CharField(blank=True, max_length=250)),
                ('alliance_id', models.IntegerField(blank=True, null=True)),
                ('corporation_id', models.IntegerField(blank=True, null=True)),
                ('owner', models.CharField(blank=True, max_length=250)),
                ('rarity', models.IntegerField(blank=True, null=True)),
                ('thirty_day_volume', models.DecimalField(decimal_places=12, max_digits=18)),
                ('thirty_day_price', models.DecimalField(decimal_places=12, max_digits=20)),
                ('met_thirty_day_price', models.DecimalField(decimal_places=12, max_digits=20)),
                ('met_thirty_day_cost', models.DecimalField(decimal_places=12, max_digits=20)),
                ('det_json', models.JSONField(default=list, null=True)),
            ],
            options={
                'db_table': 'aa_moonregistry_view',
                'managed': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='MarketPrice',
            fields=[
                ('type', models.OneToOneField(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='eve_sde.itemtype')),
                ('price', models.DecimalField(decimal_places=2, max_digits=20)),
            ],
        ),
        migrations.CreateModel(
            name='MetenoxDrillAttribute',
            fields=[
                ('name', models.CharField(max_length=25, primary_key=True, serialize=False)),
                ('value', models.DecimalField(decimal_places=5, max_digits=20)),
            ],
            options={
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='SovereigntySystem',
            fields=[
                ('system_id', models.IntegerField(primary_key=True, serialize=False)),
                ('alliance_id', models.IntegerField()),
                ('corporation_id', models.IntegerField(null=True)),
            ],
            options={
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='MarketOrder',
            fields=[
                ('order_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('price', models.FloatField()),
                ('volume_remain', models.IntegerField()),
                ('volume_total', models.IntegerField()),
                ('min_volume', models.IntegerField()),
                ('is_buy_order', models.BooleanField()),
                ('issued', models.DateTimeField()),
                ('duration', models.IntegerField()),
                ('location_id', models.IntegerField()),
                ('range', models.CharField(max_length=50)),
                ('system_id', models.IntegerField()),
                ('region_id', models.IntegerField()),
                ('pulled_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('type', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='eve_sde.itemtype')),
            ],
            options={
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='MoonDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('moon_id', models.IntegerField(db_index=True)),
                ('type_id', models.IntegerField()),
                ('quantity', models.DecimalField(decimal_places=12, max_digits=18)),
            ],
            options={
                'default_permissions': (),
                'constraints': [models.UniqueConstraint(fields=('moon_id', 'type_id'), name='uniq_moon_type')],
            },
        ),
        migrations.RunSQL(
            sql="""
                CREATE VIEW aa_moonregistry_view AS
                SELECT
                    reg.id AS region_id,
                    con.id AS constellation_id,
                    sys.id AS system_id,
                    sys.name AS system_name,
                    mn.planet_id AS planet_id,
                    mn.id AS moon_id,
                    mn.name AS moon_name,
                    alliance.alliance_id AS alliance_id,
                    corp.corporation_id AS corporation_id,
                    CONCAT(
                        alliance.alliance_ticker, ' (',
                        COALESCE(corp.corporation_ticker, ''), ')'
                    ) AS owner,
                    rarity.moon_rarity AS rarity,
                    tot.thirty_day_volume AS thirty_day_volume,
                    tot.thirty_day_price AS thirty_day_price,
                    tot.met_thirty_day_price AS met_thirty_day_price,
                    fuel_need.value * 720 * fuel_price.price
                        + cons.value * 720 * gas_price.price AS met_thirty_day_cost,
                    det.det_json AS det_json
                FROM eve_sde_moon mn
                JOIN eve_sde_planet pl
                    ON pl.id = mn.planet_id
                JOIN eve_sde_solarsystem sys
                    ON sys.id = pl.solar_system_id
                JOIN eve_sde_constellation con
                    ON con.id = sys.constellation_id
                JOIN eve_sde_region reg
                    ON reg.id = con.region_id
                LEFT JOIN aa_moonregistry_sovereigntysystem ams
                    ON ams.system_id = sys.id
                LEFT JOIN eveonline_eveallianceinfo alliance
                    ON alliance.alliance_id = ams.alliance_id
                LEFT JOIN eveonline_evecorporationinfo corp
                    ON corp.corporation_id = ams.corporation_id
                LEFT JOIN (
                    SELECT MIN(price) AS price
                    FROM aa_moonregistry_marketprice
                    WHERE type_id IN (4247, 4246, 4051, 4312)
                ) fuel_price ON 1 = 1
                LEFT JOIN aa_moonregistry_marketprice gas_price
                    ON gas_price.type_id = 81143
                LEFT JOIN aa_moonregistry_metenoxdrillattribute cons
                    ON cons.name = 'consumed_per_cycle'
                LEFT JOIN aa_moonregistry_metenoxdrillattribute fuel_need
                    ON fuel_need.name = 'module_cycle_fuel_need'
                LEFT JOIN (
                    SELECT
                        md.moon_id,
                        COALESCE(
                            JSON_ARRAYAGG(
                                JSON_OBJECT(
                                    'type_id', md.type_id,
                                    'type_name', ee_type.name,
                                    'quantity', md.quantity
                                )
                            ),
                            JSON_ARRAY()
                        ) AS det_json
                    FROM aa_moonregistry_moondetail md
                    JOIN eve_sde_itemtype ee_type
                        ON ee_type.id = md.type_id
                    GROUP BY md.moon_id
                ) det ON det.moon_id = mn.id
                LEFT JOIN (
                    SELECT
                        md.moon_id,
                        MAX(
                            CASE grp.name
                                WHEN 'Ubiquitous Moon Asteroids' THEN 4
                                WHEN 'Common Moon Asteroids' THEN 8
                                WHEN 'Uncommon Moon Asteroids' THEN 16
                                WHEN 'Rare Moon Asteroids' THEN 32
                                WHEN 'Exceptional Moon Asteroids' THEN 64
                                ELSE 0
                            END
                        ) AS moon_rarity
                    FROM aa_moonregistry_moondetail md
                    JOIN eve_sde_itemtype typ
                        ON typ.id = md.type_id
                    JOIN eve_sde_itemgroup grp
                        ON grp.id = typ.group_id
                    GROUP BY md.moon_id
                ) rarity ON rarity.moon_id = mn.id
                LEFT JOIN (
                    SELECT
                        amm.moon_id,
                        SUM(
                            30000.00 / 1000.00 * amm.quantity
                            * material.quantity * 720.00
                        ) AS thirty_day_volume,
                        SUM(
                            30000.00 / 1000.00 * amm.quantity
                            * material.quantity * 720.00 * prc.price
                        ) AS thirty_day_price,
                        SUM(
                            30000.00 / 1000.00
                            * CASE
                                WHEN material.material_item_type_id IN (35, 36)
                                    THEN 0.000
                                ELSE amm.quantity * material.quantity
                                    * 0.40000 * 720.00 * prc.price
                            END
                        ) AS met_thirty_day_price
                    FROM aa_moonregistry_moondetail amm
                    JOIN eve_sde_itemtypematerials material
                        ON material.item_type_id = amm.type_id
                    JOIN aa_moonregistry_marketprice prc
                        ON prc.type_id = material.material_item_type_id
                    GROUP BY amm.moon_id
                ) tot ON tot.moon_id = mn.id
            """,
            reverse_sql="DROP VIEW IF EXISTS aa_moonregistry_view",
        ),
    ]
