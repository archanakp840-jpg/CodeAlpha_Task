# HomeMate

A small Django ecommerce storefront for everyday home products. Customers can browse a catalog, create an account, add products to a cart, and submit orders. Staff can manage products, inventory, customers, carts, and orders through Django admin.

## Run locally (Windows PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/> for the shop or <http://127.0.0.1:8000/admin/> for administration. Add categories and products in the admin panel. Product images are uploaded to the local `media/` folder and are not committed to this repository.

Customer accounts can be created from the storefront. Staff and administrator accounts use the Staff login link; assign product change permissions to staff who should edit listings. The admin Users list shows account roles and last login. Admin log entries show recorded admin changes.

## Configuration

For local development, Django uses a development-only fallback key. Set a unique `DJANGO_SECRET_KEY` in the environment for deployment. Set `DJANGO_ALLOWED_HOSTS` to a comma-separated list of the deployment's hostnames. Do not commit secrets, the local SQLite database, or uploaded media.

## Tests

```powershell
python manage.py test store
```
