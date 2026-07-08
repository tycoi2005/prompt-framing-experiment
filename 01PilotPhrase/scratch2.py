import json

def calculate_min_wage_cost(w1, w2):
    min_cost = float('inf')
    found = False
    
    for x in range(0, 10):
        for y in range(2, 20): 
            if (x + y >= 10) and (x <= 9) and (x >= 1.5 * y):
                cost = (8 * w1 * x) + (8 * w2 * y)
                if cost < min_cost:
                    min_cost = cost
                    found = True
                    
    return min_cost if found else None

tests = [
  (50, 50),
  (100, 50),
  (60, 40),
  (40, 60),
  (10, 10),
  (150, 100),
  (200, 150)
]

for w1, w2 in tests:
    print(f"calculate_min_wage_cost({w1}, {w2}) == {calculate_min_wage_cost(w1, w2)}")
