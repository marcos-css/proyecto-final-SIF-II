"""
hash_service.py — Servicio de generación de hash SHA-256.

Este módulo contiene la función principal para calcular
la huella digital única de cualquier archivo.
"""

import hashlib


def calcular_hash(contenido: bytes) -> str:
    """
    Calcula el hash SHA-256 de un contenido binario.

    Args:
        contenido: Bytes del archivo a procesar.

    Returns:
        Cadena hexadecimal del hash SHA-256 (64 caracteres).
    """
    sha256 = hashlib.sha256()
    sha256.update(contenido)
    return sha256.hexdigest()
