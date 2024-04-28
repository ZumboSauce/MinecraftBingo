a = [1, 2, 3, 4, 5, 6]

b = [tuple([i, card]) for i in range(3) for card in a]

print(b)