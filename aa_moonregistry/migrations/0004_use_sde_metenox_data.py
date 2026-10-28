"""Read Metenox costs from eve_sde and remove the old local cache."""

from importlib import import_module

from django.db import migrations


legacy_view_sql = import_module(
    "aa_moonregistry.migrations.0001_sde_squashed"
).Migration.operations[-1].sql


class Migration(migrations.Migration):
    # MySQL/MariaDB cannot roll back view and table DDL.
    atomic = False

    dependencies = [
        ("aa_moonregistry", "0003_switch_to_eve_sde"),
    ]

    operations = [
        migrations.RunSQL(
            "DROP VIEW IF EXISTS aa_moonregistry_view",
            reverse_sql=legacy_view_sql,
        ),
        migrations.DeleteModel(name="MetenoxDrillAttribute"),
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
                        + cons.reagents_consumed_per_cycle * 720 * gas_price.price AS met_thirty_day_cost,
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
                LEFT JOIN eve_sde_metenoxmoondrill cons
                    ON cons.item_type_id = 81826
                LEFT JOIN eve_sde_typedogma fuel_need
                    ON fuel_need.item_type_id = 82941
                    AND fuel_need.dogma_attribute_id = 2109
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
