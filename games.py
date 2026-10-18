import time

Bahan_bahan = ["nasi", "telur", "cabe", "garam"]
score = 0

print("bisa nyebutin ngga apa bahan-bahan untuk membuat nasi goreng?")

Bahan_bahan_1 =input("Bahan_bahan pertama? ")
if Bahan_bahan_1 in Bahan_bahan:
    print("tepat sekali, jawabannya " + Bahan_bahan_1)
    score +=1
else:
    print("yahh, coba pikir lagi")

Bahan_bahan_2 =input("Bahan_bahan berikutnya? ")
if Bahan_bahan_2 in Bahan_bahan:
    print("kerenn jawabannya memang " + Bahan_bahan_2)
    score +=1
else:
    print("yahh, sayang sekali")


Bahan_bahan_3 =input("Bahan_bahan yang lainnya? ")
if Bahan_bahan_3 in Bahan_bahan:
    print("benar, jawabannya " + Bahan_bahan_3)
    score +=1
else:
    print("yahh, sayang sekali")

print("game over, nilaimu " + str(score) + " points" " lumayan lah ya")
print("ini Bahan_bahan yang benar!")
print("Bahan_bahan list was:")
print(Bahan_bahan)