# Moon Registry for Alliance Auth

This is a Moon Registry app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA) 


## Features

- Search all moons across Eve once imported, by (system, constellation, region), ore, sov. owner, rarity
- Add moon scans via parsed text

## Installation

Before installing Moon Registry, install and configure `django-eveonline-sde`
(`eve_sde`) in Alliance Auth. Complete its migrations and run `esde_load_sde`
successfully. The SDE load must include regions, constellations, solar systems,
item types, type materials, planets, and moons. Follow the SDE package's setup
instructions, including its `modeltranslation` requirement.

In your Alliance Auth virtual environment, install Moon Registry in editable
mode from a local checkout:

```bash
pip install -e {path_to}/aa_moonregistry
```

or via PyPi:

```bash
pip install aa_moonregistry
```

Add `aa_moonregistry` to `INSTALLED_APPS` in `settings/local.py`.

Apply Moon Registry's migrations. On upgrades, existing moon scans and cached
prices keep their EVE type IDs.

```bash
python manage.py migrate
```

Load initial Eve sovereignty

```bash
python manage.py aa_moonregistry_load_sovereignty
```

Load initial JITA IV material pricing. Calculates average of top 5 JBV per type 

```bash
python manage.py aa_moonregistry_load_jita_materials_prices
```

Next copy all the static data to the output folder

```bash
python manage.py collectstatic --noinput
```

Finally restart your AA setup.

## Permissions

There is only one access level that will give access to the app in menu
    *aa_moonregistry.basic_access*


## Alliance Auth Tasks

There are several registered tasks that should be run periodically.

*aa_moonregistry.tasks.refresh_sovereignty* - Reloads current Eve Sovereignty. Schedule once a week or so.

*aa_moonregistry.tasks.refresh_material_prices* - Refreshes pricing for calculations. Schedule once per day.
