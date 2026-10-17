# Deploying to PythonAnywhere (free Beginner account)

The site ends up at `https://yourusername.pythonanywhere.com`, where `yourusername` is
your PythonAnywhere username (in lowercase).

Free Beginner accounts don't include MySQL, so the hosted site uses SQLite
(`DB_ENGINE=sqlite`). Every page and chart works the same as with MySQL.

**Free account limits:**
- one web app;
- 512 MB of disk (the project and its virtualenv take about 90 MB);
- 100 CPU-seconds a day (loading the demo data takes about one);
- the site must be renewed from the **Web** tab before the expiry date shown there.

## 0. Before you start

- Push your latest commits to `main` on GitHub. PythonAnywhere clones from there, and
  `config/settings.py` must include the `DB_ENGINE` switch.
- Sign up at [pythonanywhere.com](https://www.pythonanywhere.com/) with a **Beginner** (free) account.

## 1. Create the web app

On the **Web** tab, click **Add a new web app**, then **Next**, then
**Manual configuration** (not "Django", which would start an empty project), then
**Python 3.13**, then **Next**.

## 2. Download the project and install packages

Open **Consoles → Bash** and run:

```bash
git clone https://github.com/NNesta/Hospital-Management-System-and-Data-Analytics.git
cd Hospital-Management-System-and-Data-Analytics
mkvirtualenv --python=/usr/bin/python3.13 hms-venv
pip install -r requirements.txt
```

This takes a few minutes. If `python3.13` is not found, choose the newest system image
under **Account → System image** and try again. If `mysqlclient` fails to build, skip it
(SQLite doesn't need it):
`pip install Django==5.2.18 python-decouple==3.8 Faker==40.43.0`.

## 3. Configure and load the demo data

In the same console, paste this whole block. It works out your site address from your
username, writes `.env` with a new secret key, builds the database, loads the demo data,
collects the static files and writes the web app's WSGI file:

```bash
workon hms-venv
cd ~/Hospital-Management-System-and-Data-Analytics
SITE=$(echo "$USER" | tr '[:upper:]' '[:lower:]').pythonanywhere.com
cat > .env <<EOF
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
DEBUG=False
ALLOWED_HOSTS=$SITE
CSRF_TRUSTED_ORIGINS=https://$SITE
HTTPS_ONLY=True
DB_ENGINE=sqlite
EOF
python manage.py migrate
python manage.py seed_data
python manage.py collectstatic --noinput
cat > /var/www/${SITE//./_}_wsgi.py <<EOF
import os
import sys

path = "$PWD"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
EOF
echo "Source code:   $PWD"
echo "Virtualenv:    $VIRTUAL_ENV"
echo "Static files:  URL /static/   Directory $PWD/staticfiles"
```

Keep the last three lines it prints for the next step.

## 4. Connect the web app to the project

Back on the **Web** tab, fill in the values the console printed:

| Section | Setting |
|---|---|
| Code | **Source code**: the `Source code` path |
| Virtualenv | the `Virtualenv` path (`/home/yourusername/.virtualenvs/hms-venv`) |
| Static files | **URL** `/static/`, **Directory** the `staticfiles` path |
| Security | **Force HTTPS**: Enabled |

Click the green **Reload** button at the top, open `https://yourusername.pythonanywhere.com`
and sign in as `admin` / `Ubuzima@2026`.

## Updating the site later

After pushing new commits to GitHub, run in a Bash console:

```bash
workon hms-venv
cd ~/Hospital-Management-System-and-Data-Analytics
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Then click **Reload** on the **Web** tab. Before a demo, run
`python manage.py seed_data --reset` so today's clinic list is current.

## If something goes wrong

- **"Something went wrong" page or 500 errors**: open the **error log** linked on the
  Web tab. A `DisallowedHost` error means `ALLOWED_HOSTS` in `.env` doesn't match the
  address in the browser.
- **"No module named django"**: the Virtualenv path on the Web tab is wrong or empty.
- **Pages load without styling**: check the `/static/` mapping, check that `collectstatic`
  ran, then reload.
- **"CSRF verification failed" when signing in**: check that `CSRF_TRUSTED_ORIGINS` in
  `.env` starts with `https://` and that **Force HTTPS** is on.
- **Changes to `.env` or the code have no effect**: click **Reload**.
- **Site switched off**: free web apps expire unless renewed. Click the button on the Web
  tab to extend it, then reload.

## Using MySQL instead (paid accounts)

Paid accounts, and free accounts created before 15 January 2026, include MySQL. On the
**Databases** tab, set a MySQL password and create a database called `hospital_db`.
Then, in `.env`, replace `DB_ENGINE=sqlite` with the following lines and run
`python manage.py migrate` and `python manage.py seed_data` again:

```ini
DB_NAME=yourusername$hospital_db
DB_USER=yourusername
DB_PASSWORD=the-mysql-password
DB_HOST=yourusername.mysql.pythonanywhere-services.com
```
