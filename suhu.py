temperatur = 0.0
ac = 0.0
heater = 0.0

temperatur = float(input("masukkan suhu:"))

if temperatur < 20.0:
    heater = 1.0
    print("kondisi heater = ", heater)
elif temperatur >= 20.0 and temperatur <= 25.0:
    print("kodisi stabil")
    print("heater = ", heater, "ac =", ac)
elif temperatur >25.0:
    ac = 1.0
    print("kondisi ac = ", ac)