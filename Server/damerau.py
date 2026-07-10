def damerau_levenshtein(a: str, b: str, max_dist: int | None = None) -> int:
    len_a, len_b = len(a), len(b)

    if max_dist is not None and abs(len_a - len_b) > max_dist:
        return max_dist + 1

    dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]

    for i in range(len_a + 1):
        dp[i][0] = i

    for j in range(len_b + 1):
        dp[0][j] = j

    for i in range(1, len_a + 1):
        row_min = float("inf")

        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )

            if (
                i > 1 and j > 1 and
                a[i - 1] == b[j - 2] and
                a[i - 2] == b[j - 1]
            ):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

            row_min = min(row_min, dp[i][j])

        if max_dist is not None and row_min > max_dist:
            return max_dist + 1

    return dp[len_a][len_b]


def fuzzy_search(text: str, pattern: str, similarity: float):
    results = []

    pattern = pattern.lower()
    text_lower = text.lower()

    m = len(pattern)
    max_dist = int((1.0 - similarity) * m)

    min_len = max(1, m - max_dist)
    max_len = m + max_dist

    for i in range(len(text_lower)):
        for size in range(min_len, max_len + 1):
            if i + size > len(text_lower):
                continue

            candidate = text_lower[i:i + size]
            dist = damerau_levenshtein(pattern, candidate, max_dist)

            if dist <= max_dist:
                results.append(i)
                break

    return results