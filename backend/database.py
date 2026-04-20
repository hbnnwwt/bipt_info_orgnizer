# backend/database.py
# Delegates to bipthelper's database.py using absolute import path

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "bp_database",
    "E:/code/bipthelper/backend/database.py",
    submodule_search_locations=["E:/code/bipthelper/backend"]
)
bp_db = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp_db)

get_session = bp_db.get_session
create_db_and_tables = bp_db.create_db_and_tables