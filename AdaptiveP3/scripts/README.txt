PostgreSQL setup scripts
=========================

1) Install PostgreSQL (if not installed):
   https://www.postgresql.org/download/windows/

2) Open 'SQL Shell (psql)' and log in as the superuser (usually 'postgres').

3) Run:
   \i 'C:/Users/aadha/Documents/VSCode/AdaptiveP3/scripts/01-create-db.sql'

4) Switch to the new database:
   \c ap3_db

5) Run:
   \i 'C:/Users/aadha/Documents/VSCode/AdaptiveP3/scripts/02-seed.sql'

Credentials used in the scripts:
- user: ap3_user
- password: ap3_password
- database: ap3_db

Update config.py or set env vars to match these values.
