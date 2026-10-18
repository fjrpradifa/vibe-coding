def tampilkan_menu():
    print("   SELAMAT DATANG DI KALKULATOR")
    print("Masukkan 2 angka dan pilih operasi.")
    print("Penjumlahan : +")
    print("Pengurangan : -")
    print("Perkalian   : *")
    print("Pembagian   : /")


# Fungsi dengan input (parameter a dan b) dan output (return)
def tambah(a, b):
    return a + b

def kurang(a, b):
    return a - b

def kali(a, b):
    return a * b

def bagi(a, b):
    if b == 0:
        return "tidak bisa dibagi nol"
    return a / b


# Fungsi ini memanggil fungsi lain (tambah, kurang, kali, bagi)
def hitung(a, b, operasi):
    if operasi == "+":
        return tambah(a, b)
    elif operasi == "-":
        return kurang(a, b)
    elif operasi == "*":
        return kali(a, b)
    elif operasi == "/":
        return bagi(a, b)
    else:
        return "operasi tidak dikenal"


# Fungsi utama memanggil tampilkan_menu() dan hitung()
def main():
    tampilkan_menu()
    a = int(input("Masukkan angka pertama: "))
    b = int(input("Masukkan angka kedua: "))
    operasi = input("Pilih operasi (+, -, *, /): ")

    hasil = hitung(a, b, operasi)
    print("Hasil:", a, operasi, b, "=", hasil)


main()