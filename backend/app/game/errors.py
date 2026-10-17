class InvalidTransition(Exception):
    """El estado actual no permite la transición pedida: es un bug del llamador."""
