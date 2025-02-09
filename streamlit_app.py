import sqlite3  # SQLite kütüphanesi
import requests
from bs4 import BeautifulSoup
import streamlit as st
import json
import csv
from docx import Document
import io
import time
import threading


# Oyunun ismini çekme
def get_game_name(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get(str(app_id), {}).get('success', False):
            return data[str(app_id)]['data']['name']
    return "Böyle bir oyun yok..."


# İncelemeleri çekme
def get_steam_reviews(app_id, num_pages=10):
    base_url = f"https://steamcommunity.com/app/{app_id}/reviews/"
    reviews = []

    status_text = st.empty()
    loading = True

    def loading_animation():
        dots = ["", ".", "..", "..."]
        i = 0
        while loading:
            status_text.write(f"Taranıyor{dots[i]}")
            i = (i + 1) % len(dots)
            time.sleep(0.5)

    thread = threading.Thread(target=loading_animation)
    thread.start()

    for page in range(1, num_pages + 1):
        url = f"{base_url}?p={page}&browsefilter=mostrecent"
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Sayfa {page} alınamadı. Durum kodu: {response.status_code}")
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        review_blocks = soup.find_all('div', class_='apphub_CardTextContent')
        for block in review_blocks:
            review_text = block.get_text(strip=True)
            reviews.append(review_text)

    loading = False
    thread.join()
    status_text.write("İncelemeler başarıyla çekildi!")

    return reviews


# Word olarak kaydetme
def save_as_word(app_id):
    game_name = get_game_name(app_id)
    reviews = get_steam_reviews(app_id)

    if not reviews:
        st.warning("Kaydedilecek bir inceleme bulunamadı.")
        return

    document = Document()
    document.add_heading(f"Reviews for '{game_name}' (App ID: {app_id})", level=1)

    for i, review in enumerate(reviews, start=1):
        document.add_paragraph(f"Review {i}:")
        document.add_paragraph(review)
        document.add_paragraph()

    byte_io = io.BytesIO()
    document.save(byte_io)
    byte_io.seek(0)

    st.success(f"📝 **{game_name}** oyununun incelemeleri Word formatında indirilebilir!")
    st.download_button(
        label="Word dosyasını indir",
        data=byte_io,
        file_name=f"{game_name}_reviews.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# JSON olarak kaydetme
def save_as_json(app_id):
    game_name = get_game_name(app_id)
    reviews = get_steam_reviews(app_id)

    if not reviews:
        st.warning("Kaydedilecek bir inceleme yok.")
        return

    json_data = json.dumps({"App ID": app_id, "Game Name": game_name, "Reviews": reviews}, indent=4, ensure_ascii=False)

    st.success(f"📝 **{game_name}** oyununun incelemeleri JSON formatında indirilebilir!")
    st.download_button(
        label="JSON dosyasını indir",
        data=json_data,
        file_name=f"{game_name}_reviews.json",
        mime="application/json"
    )


import csv
import io


# CSV olarak kaydetme
def save_as_csv(app_id):
    if not app_id.isdigit():
        st.error("App ID bir sayı olmalı!")
        return

    game_name = get_game_name(app_id)
    reviews = get_steam_reviews(app_id)

    if not reviews:
        st.warning("Kaydedilecek bir inceleme yok.")
        return

    # CSV'yi bellekte oluştur (BytesIO kullanıyoruz!)
    byte_io = io.BytesIO()
    text_io = io.TextIOWrapper(byte_io, encoding="utf-8", newline="")

    # CSV yazma işlemi
    csv_writer = csv.writer(text_io)
    csv_writer.writerow(["App ID", "Game Name", "Review"])

    for review in reviews:
        csv_writer.writerow([app_id, game_name, review])

    # Streamlit için dosyayı sıfırdan okumaya hazır hale getir
    text_io.flush()
    byte_io.seek(0)

    st.success(f"📄 **{game_name}** oyununun incelemeleri CSV formatında indirilebilir!")

    # Kullanıcıya indirme butonu sun
    st.download_button(
        label="CSV dosyasını indir",
        data=byte_io.getvalue(),
        file_name=f"{game_name}_reviews.csv",
        mime="text/csv"
    )

def update_game_name():
    app_id = st.session_state.app_id.strip()  # Boşlukları temizle
    if app_id.isdigit() and app_id:
        st.session_state.game_name = get_game_name(app_id)
    else:
        st.session_state.game_name = "Geçerli bir App ID girin"

# Kullanıcı Arayüzü
st.title("Steam Review Scraper")

st.write("Oyunun App ID'sini giriniz: ")
st.text_input("App ID", key="app_id", on_change=update_game_name)

app_id = st.session_state.app_id  # App ID'yi tekrar kullanmak için değişkene ata

if "game_name" in st.session_state:
    st.markdown(f"🎮 **Oyun Adı:** `{st.session_state.game_name}`")
else:
    st.warning("App ID'yi yazın ve geçerli bir ID girildiğinden emin olun.")

# Butonları ortalamak için HTML ve CSS
st.markdown(
    """
    <style>
    .centered {
        display: flex;
        justify-content: center;
        gap: 20px; /* Butonlar arasındaki mesafe */
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Butonları içine koyacağımız div başlıyor
st.markdown('<div class="centered">', unsafe_allow_html=True)

# Butonları üç sütun içine koyuyoruz
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Word olarak kaydet"):
        save_as_word(app_id)

with col2:
    if st.button("JSON olarak kaydet"):
        save_as_json(app_id)

with col3:
    if st.button("CSV olarak kaydet"):
        save_as_csv(app_id)

# Div kapatılıyor
st.markdown('</div>', unsafe_allow_html=True)





st.write("Aradığınız Oyunun App ID'sini öğrenmek için tıklayın.")
st.markdown("[SteamDB](https://steamdb.info/apps/)", unsafe_allow_html=True)