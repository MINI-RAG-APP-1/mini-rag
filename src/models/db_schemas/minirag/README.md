## Run Alembic Configurations

```bash
cp alembic.ini.example alembic.ini
```

- Update `alembic.ini` with your database credintials (`sqlalchemy.url`)

### (Optional) Create a new migration

```bash
alembic revision --autogenerate -m "Add ..."
```

### Upgrade the database

```bash
alembic upgrade head
```
