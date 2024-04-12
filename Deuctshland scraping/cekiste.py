import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_day_names():
    day_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return day_names

def add_day_names_to_hours(saat_bilgileri):
    day_names = get_day_names()
    saatler_with_days = []
    for i, saat in enumerate(saat_bilgileri):
        day_name = day_names[i % 7] 
        saat_with_day = f"{day_name}: {saat}"
        saatler_with_days.append(saat_with_day)
    return saatler_with_days

url = "https://www.dasoertliche.de/?zvo_ok=0&plz=&quarter=&district=&ciid=&kw=Friseure&ci=&kgs=&buab=&zbuab=&form_name=search_nat&recFrom={page_num}"

def sokakKapIAyrıstır(adres):
    regex_deseni = r'(.+?)\s*(\d+)(?:\s*(\w))?'
    
    # Desen eşleştirmesi yapma
    eslestirme = re.match(regex_deseni, adres)

    if eslestirme:
        sokak = eslestirme.group(1)
        kapi_numarasi = eslestirme.group(2)
        if eslestirme.group(3):
            kapi_ek = eslestirme.group(3)
            kapi_numarasi = kapi_numarasi + " " + kapi_ek
            return sokak, kapi_numarasi
        else:
            return sokak, kapi_numarasi
    else:
        print("Adres deseni eşleşmedi.")
        return '', ''

def PstaKoduSehirAyristir(adres):
    # Regex deseni oluşturma
    regex_deseni = r'(\d{5})\s+(.+)$'
    
    # Desen eşleştirmesi yapma
    eslestirme = re.match(regex_deseni, adres)

    if eslestirme:
        posta_kodu = eslestirme.group(1)
        sehir = eslestirme.group(2)
        return posta_kodu, sehir
    else:
        return '', ''

start = 1
end = 51351  # 51351

linkler = []
bilgiler = []

for page_num in range(start, end, 25):  # Sayfa numarası artışı kontrol edilmeli
    response = requests.get(url.format(page_num=page_num))
    soup = BeautifulSoup(response.content, 'html.parser')

    for href, category in zip(soup.find_all('a', class_="hitlnk_name"), soup.find_all('div', class_="category")):
        linkler.append((href['href'], category.text.strip()))
        print(href['href'])
    time.sleep(1)

for link, kategori in linkler:
    time.sleep(1)
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')

    isim = soup.find('div', class_="name").text.strip() if soup.find('div', class_="name") else "isim yok"
    
    # Adres bilgileri
    adres = soup.find('div', class_="det_address")
    address_p = soup.find('div', class_="det_address")
    address_parts = address_p.get_text(separator="\n", strip=True).split('\n')
    
    sokak_kapi = address_parts[0]
    posta_sehir = address_parts[1]

    print(sokak_kapi ,posta_sehir)

    sokak, kapi_numarasi = sokakKapIAyrıstır(sokak_kapi)
    posta_kodu, sehir = PstaKoduSehirAyristir(posta_sehir)
    
    
    numara = soup.select_one('table.det_numbers span').text.strip() if soup.select_one('table.det_numbers span') else "numara yok"
    email = soup.find('a', class_="mail").text.strip() if soup.find('a', class_="mail") else "email yok"
    
    # Saat bilgilerini çekme
    saat_bilgileri = []
    for tr in soup.select('table.bordered.det_contcol_left tr:not(:first-child)'):
        saat_td = tr.find_all('td')[1]
        if saat_td:
            saat = saat_td.text.strip() 
            saat_bilgileri.append(saat)
        else:
            saat_bilgileri.append("Saat Bilgisi Yok")

    saatler_with_days = add_day_names_to_hours(saat_bilgileri)
    

    print(f"İsim: {isim}\n\nNumara: {numara}\nKapı no:{kapi_numarasi}\nKategori: {kategori}\nPosta Kodu:{posta_kodu}\nŞehir:{sehir}\nSokak:{sokak}\nE-mail: {email}\nCalisma Saatleri:")
    
    print(saat)
    print("-" * 50)

    # Her bir işletmenin bilgilerini bir sözlük olarak sakla
    ürün = {
        'İsim': isim,
        'Sokak':sokak,
        'Kapı no':kapi_numarasi,
        'Posta Kodu':posta_kodu,
        'Şehir':sehir,
        'Numara': numara,
        'Kategori': kategori,
        'E-mail': email,
        'Calisma Saatleri': '; '.join(saatler_with_days)
    }

    bilgiler.append(ürün)

# Pandas DataFrame oluştur ve Excel'e kaydet
df = pd.DataFrame(bilgiler)
df.to_excel(f'Friseure_{start}_{end}.xlsx', index=False)
