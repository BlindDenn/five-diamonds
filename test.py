from datetime import date


records = [ 
    {"date": date(2025, 11, 24), "number": 21},
    {"date": date(2025, 11, 23), "number": 19},
    {"date": date(2024, 11, 22), "number": 19},
    ]

records_sorted = sorted(records, key=lambda record: record["date"])

print(records_sorted)

current_date = date.today()
print(current_date, type(current_date))

for i in range(0, -len(records_sorted), -1):
    print(i - 1)
    print(records_sorted[i - 1]["date"])
    if records_sorted[i - 1]["date"] == current_date:
        print("Искомая запись: ", records_sorted[i - 1]["date"])
        break

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
numbers_odd = list(filter(lambda x: x % 2 == 1, numbers))

print(numbers_odd)

nubers_sqr = list(map(lambda x: x*x, numbers ))
print(nubers_sqr)
