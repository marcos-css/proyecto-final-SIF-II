"""
verification_service.py — Servicio de verificación de integridad.

Compara el hash SHA-256 de un archivo sospechoso contra
el hash original almacenado en la base de datos.
"""

from app.services.hash_service import calcular_hash


def verificar_integridad(contenido_sospechoso: bytes, hash_original: str) -> dict:
    """
    Verifica si un archivo sospechoso coincide con el registro original.

    Args:
        contenido_sospechoso: Bytes del archivo a verificar.
        hash_original: Hash SHA-256 almacenado en la base de datos.

    Returns:
        Diccionario con:
            - integro (bool): True si los hashes coinciden.
            - hash_original (str): El hash almacenado.
            - hash_sospechoso (str): El hash calculado del archivo sospechoso.
    """
    hash_sospechoso = calcular_hash(contenido_sospechoso)

    return {
        "integro": hash_sospechoso == hash_original,
        "hash_original": hash_original,
        "hash_sospechoso": hash_sospechoso,
    }
