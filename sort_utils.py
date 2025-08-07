def merge_sort(arr):
    """
    Esegue il Merge Sort su una lista arr e ne ritorna
    una nuova versione ordinata.
    Complessità: O(n log n)
    """
    # Caso base: liste di lunghezza 0 o 1 sono già ordinate
    if len(arr) <= 1:
        return arr

    # 1) Divide: trova il punto medio e spezza in due metà
    mid = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    # 2) Conquista: fonde le due metà ordinate
    return _merge(left, right)


def _merge(left, right):
    """
    Fonde due liste già ordinate (left e right) in una sola lista
    ordinata e la ritorna.
    """
    merged = []
    i = j = 0

    # Confronta gli elementi in testa alle due liste
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    # Se avanzano resti di left o right, aggiungili tutti
    if i < len(left):
        merged.extend(left[i:])
    if j < len(right):
        merged.extend(right[j:])

    return merged


# ─────────────────────────────────────────────────────────────────────
# Esempio d’uso
if __name__ == "__main__":
    dati = [38, 27, 43, 3, 9, 82, 10]
    print("Prima:", dati)
    ordinati = merge_sort(dati)
    print("Dopo:", ordinati)
