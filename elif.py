makanan = ["ayam", "bebek", "sapi"]

masukan = input("cari menu: ").lower()

if masukan in makanan:
    print("menu tersedia") 

else:
    print("menu kosong")