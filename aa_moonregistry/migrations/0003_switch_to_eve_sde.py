"""Move existing installations' view and cached type relations to the SDE."""

from copy import copy
from importlib import import_module

from django.db import migrations


def remove_legacy_type_constraints(apps, schema_editor):
    """Keep cached prices and orders while their type IDs move to SDE."""
    connection = schema_editor.connection
    for model_name in ("MarketOrder", "MarketPrice"):
        model = apps.get_model("aa_moonregistry", model_name)
        table = model._meta.db_table
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        has_legacy_fk = any(
            details.get("foreign_key", (None,))[0] == "eveuniverse_evetype"
            for details in constraints.values()
            if details.get("foreign_key")
        )
        if has_legacy_fk:
            field = model._meta.get_field("type")
            old_field = copy(field)
            old_field.db_constraint = True
            schema_editor.alter_field(model, old_field, field)


# The replacement migration is self-contained and is also used to build the
# same view for databases which already applied the original migrations.
view_sql = import_module(
    "aa_moonregistry.migrations.0001_sde_squashed"
).Migration.operations[-1].sql


class Migration(migrations.Migration):
    # MySQL/MariaDB cannot roll back DDL such as DROP VIEW or DROP FOREIGN KEY.
    atomic = False

    dependencies = [
        ("aa_moonregistry", "0001_sde_squashed"),
    ]

    operations = [
        migrations.RunSQL("DROP VIEW IF EXISTS aa_moonregistry_view"),
        migrations.RunPython(
            remove_legacy_type_constraints,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunSQL(view_sql, reverse_sql="DROP VIEW IF EXISTS aa_moonregistry_view"),
    ]
