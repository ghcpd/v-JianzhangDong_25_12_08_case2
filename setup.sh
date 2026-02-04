#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# initialize a test database and config directory
python - <<'PY'
import sqlite3, os
db='appdata.db'
if not os.path.exists(db):
    conn=sqlite3.connect(db)
    c=conn.cursor()
    c.execute('CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
    c.execute("INSERT INTO profiles (name, balance) VALUES ('Alice', 100.0)")
    c.execute("INSERT INTO profiles (name, balance) VALUES ('Bob', 50.0)")
    conn.commit(); conn.close()

os.makedirs('configs', exist_ok=True)
open('configs/default.yml','w').write('example: true\n')
print('Environment and test data set up.')
PY