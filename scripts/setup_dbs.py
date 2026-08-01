#!/usr/bin/env python3
# =============================================================================
# setup_dbs.py — Genera las bases de datos de ambas versiones en db/
#
#   db/v1_academico.db  -> V1 (vulnerable): passwords en TEXTO PLANO
#                          (admin/admin123, profesor/profesor). Objetivo de sqlmap.
#   db/v2_academico.db  -> V2 (segura): passwords con bcrypt.
#
# Uso:
#   python scripts/setup_dbs.py
# =============================================================================
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, 'db')
V1_DIR = os.path.join(BASE_DIR, 'v1')
V2_DB = os.path.join(DB_DIR, 'v2_academico.db')
V1_DB = os.path.join(DB_DIR, 'v1_academico.db')


def main():
    os.makedirs(DB_DIR, exist_ok=True)

    print('[1/2] Generando V2 (bcrypt): db/v2_academico.db')
    env = dict(os.environ, DATABASE_URL=os.path.join('db', 'v2_academico.db'))
    subprocess.check_call(
        [sys.executable, 'init_db.py'],
        cwd=BASE_DIR, env=env,
    )

    print('[2/2] Generando V1 (texto plano): db/v1_academico.db')
    subprocess.check_call(
        [sys.executable, 'init_db.py'],
        cwd=V1_DIR,
    )
    shutil.copyfile(os.path.join(V1_DIR, 'academico.db'), V1_DB)

    print()
    print('Bases de datos listas:')
    for db in (V1_DB, V2_DB):
        size = os.path.getsize(db)
        print(f'  - {db} ({size} bytes)')
    print()
    print('V1 (texto plano):  admin/admin123, profesor/profesor')
    print('V2 (bcrypt):       admin/admin123, profesor/profesor')
    print()
    print('Nota: las BDs en db/ estan versionadas (!db/*.db en .gitignore).')


if __name__ == '__main__':
    main()
