def evaluate(answer, guess, mode="vi", strict=False):
    result = ["gray"] * len(guess)
    used = [False] * len(answer)

    # Green
    for i in range(len(guess)):
        if guess[i] == answer[i]:
            result[i] = "green"
            used[i] = True

    # Yellow
    for i in range(len(guess)):
        if result[i] == "green":
            continue
        for j in range(len(answer)):
            if not used[j] and guess[i] == answer[j]:
                result[i] = "yellow"
                used[j] = True
                break

    return result