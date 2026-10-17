# Moon Registry for Alliance Auth

This is a Moon Registry app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA) 


## Features

- Search all moons across Eve once imported, by (system, constellation, region), ore, sov. owner, rarity
- Add moon scans via parsed text

## Installation

Once you have cloned the repo or copied all files into place.

Make sure you are in your venv. Then install it with pip in editable mode:

```bash
pip install -e {path_to}/aa_moonregistry
```

First add your app to the Django project by adding 'aa_moonregistry' to INSTALLED_APPS in `settings/local.py`.

Next perform migrations to add models to the database:

```bash
python manage.py migrate
```

Next load all the planets and moons from via eve universe, if not loaded already. This will take a while!!

```bash
python manage.py aa_moonregistry_load_planets_moons
```

Load initial Eve sovereignty

```bash
python manage.py aa_moonregistry_load_sovereignty
```

Load Metenox-specific fuel data

```bash
python manage.py aa_moonregistry_load_metenox_data
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

