# -*- coding: utf-8 -*-
"""
api/index.py
Adaptador para desplegar en Vercel (runtime @vercel/python).
Vercel espera encontrar una variable WSGI llamada `app` en este módulo;
simplemente reexportamos la app Flask real que vive en la raíz del proyecto.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402  (la app Flask real)
