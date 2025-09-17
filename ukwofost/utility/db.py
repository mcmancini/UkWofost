# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), September 2025
# =========================================================
"""
db.py
=====
Database utility functions
"""
import os
import urllib

from sqlalchemy import create_engine


def create_db_connection(app_config):
    """Create a database connection using SQLAlchemy."""
    db_name = os.path.expandvars(app_config.db_parameters.get("db_name", ""))
    db_name = None if not db_name else db_name
    db_user = os.path.expandvars(app_config.db_parameters.get("username", ""))
    db_user = None if not db_user else db_user
    db_password = os.path.expandvars(
        app_config.db_parameters.get("password", "")
    )
    db_host = os.path.expandvars(app_config.db_parameters.get("host", ""))
    db_password = (
        None if not db_password else urllib.parse.quote_plus(db_password)
    )

    database_url = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:5432/{db_name}"
    )

    engine = create_engine(
        database_url,
        pool_size=300,  # adjust depending on expected load
        max_overflow=100,  # how many extra connections if pool is full
        pool_timeout=30,  # wait time before giving up on a connection
        pool_recycle=1800,  # refresh connections periodically
    )
    return engine
