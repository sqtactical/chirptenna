"""Lector mínimo de expresiones S (el formato de los ficheros de KiCad).

`leer(texto)` devuelve listas anidadas: un átomo es `str` (o `float` si es un número sin comillas) y una cadena entre
comillas es un `Cadena` (subclase de `str`, para distinguir `"F.Cu"` de `F.Cu` si hace falta). Sin dependencias, para
que funcione también en la versión web.
"""


class Cadena(str):
    """Texto que venía entre comillas."""


def _numero(t):
    try:
        return float(t)
    except ValueError:
        return t


def leer(texto):
    """Primera expresión del texto, como listas anidadas."""
    pila, actual, i, n = [], None, 0, len(texto)
    raiz = None
    while i < n:
        c = texto[i]
        if c in ' \t\r\n':
            i += 1
        elif c == '(':
            nueva = []
            if actual is not None:
                actual.append(nueva)
                pila.append(actual)
            actual = nueva
            if raiz is None:
                raiz = nueva
            i += 1
        elif c == ')':
            if actual is None:
                raise ValueError('paréntesis de cierre sin abrir')
            actual = pila.pop() if pila else None
            i += 1
            if actual is None:
                break
        elif c == '"':
            j, partes = i + 1, []
            while j < n and texto[j] != '"':
                if texto[j] == '\\' and j + 1 < n:
                    j += 1
                partes.append(texto[j])
                j += 1
            if j >= n:
                raise ValueError('cadena sin cerrar')
            if actual is None:
                raise ValueError('texto fuera de una expresión')
            actual.append(Cadena(''.join(partes)))
            i = j + 1
        else:
            j = i
            while j < n and texto[j] not in ' \t\r\n()':
                j += 1
            if actual is None:
                raise ValueError('texto fuera de una expresión')
            actual.append(_numero(texto[i:j]))
            i = j
    if raiz is None or actual is not None:
        raise ValueError('expresión vacía o sin cerrar')
    return raiz


def hijos(nodo, nombre):
    """Sub-listas de `nodo` cuyo primer elemento es `nombre`."""
    return [h for h in nodo if isinstance(h, list) and h and h[0] == nombre]


def hijo(nodo, nombre):
    """Primera sub-lista llamada `nombre`, o None."""
    for h in nodo:
        if isinstance(h, list) and h and h[0] == nombre:
            return h
    return None
