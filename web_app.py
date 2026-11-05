import streamlit as st
import sqlite3
import pandas as pd

# 1. Sayfa ve Mobil Uyum Ayarları
st.set_page_config(page_title="Pro Oran Analiz", page_icon="⚽", layout="wide")

# 2. Şifre Koruması (Sadece sana özel)
st.sidebar.title("🔒 Sisteme Giriş")
sifre = st.sidebar.text_input("Erişim Şifresi:", type="password")

if sifre != "proanaliz2026":
    st.warning("Lütfen sistemi kullanmak için sol menüden şifrenizi giriniz.")
    st.stop()

# 3. Ana Arayüz (Şifre doğruysa görünür)
st.title("📊 Geçmiş Oran Eşleştirme Motoru")
st.markdown("---")

def skor_cevir(ev, dep):
    if pd.isna(ev) or pd.isna(dep): return "Belirsiz"
    if ev > dep: return "1"
    elif ev == dep: return "0"
    else: return "2"

# Kullanıcı Girdileri
col1, col2, col3 = st.columns(3)
with col1:
    h1_str = st.text_input("MS 1 Oranı", "1.90")
with col2:
    h0_str = st.text_input("MS 0 Oranı", "3.40")
with col3:
    h2_str = st.text_input("MS 2 Oranı", "4.00")

esnek_arama = st.checkbox("Esnek Arama Kullan (±0.05 Tolerans)", value=True)

if st.button("🚀 Verileri Analiz Et", use_container_width=True):
    try:
        h1 = float(h1_str.replace(',', '.'))
        h0 = float(h0_str.replace(',', '.'))
        h2 = float(h2_str.replace(',', '.'))
    except ValueError:
        st.error("Lütfen geçerli sayılar giriniz!")
        st.stop()

    tolerans = 0.05 if esnek_arama else 0.0

    try:
        conn = sqlite3.connect("futbol_arsiv.db")
        if tolerans > 0:
            query = f"""SELECT * FROM maclar WHERE B365_Kapanis_1 BETWEEN {h1-tolerans} AND {h1+tolerans} 
                        AND B365_Kapanis_0 BETWEEN {h0-tolerans} AND {h0+tolerans} 
                        AND B365_Kapanis_2 BETWEEN {h2-tolerans} AND {h2+tolerans}"""
        else:
            query = f"""SELECT * FROM maclar WHERE B365_Kapanis_1 = {h1} AND B365_Kapanis_0 = {h0} AND B365_Kapanis_2 = {h2}"""
        df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        st.error(f"Veritabanı hatası: {e}")
        st.stop()

    toplam_mac = len(df)
    if toplam_mac == 0:
        st.error("❌ Bu oranlara uygun geçmiş maç bulunamadı.")
    else:
        st.success(f"✅ Eşleşen Toplam Maç Sayısı: {toplam_mac}")
        
        # Analiz Hesaplamaları
        df['IY_Sonuc'] = df.apply(lambda row: skor_cevir(row['IY_Skor_Ev'], row['IY_Skor_Dep']), axis=1)
        df['MS_Sonuc'] = df.apply(lambda row: skor_cevir(row['Skor_Ev'], row['Skor_Dep']), axis=1)
        df['IY_MS'] = df['IY_Sonuc'] + "/" + df['MS_Sonuc']
        df['Tam_Skor'] = df.apply(lambda row: f"{int(row['Skor_Ev'])}-{int(row['Skor_Dep'])}" if not pd.isna(row['Skor_Ev']) else "Belirsiz", axis=1)
        
        df['Toplam_Gol'] = df['Skor_Ev'] + df['Skor_Dep']
        ust = len(df[df['Toplam_Gol'] > 2.5])
        alt = toplam_mac - ust
        kg_var = len(df[(df['Skor_Ev'] > 0) & (df['Skor_Dep'] > 0)])
        kg_yok = toplam_mac - kg_var

        tab1, tab2 = st.tabs(["📈 Analiz Özeti", "📋 Tüm Eşleşen Maçlar"])
        
        with tab1:
            st.subheader("🔥 Öne Çıkan Trendler")
            gecerli_skorlar = df[df['Tam_Skor'] != "Belirsiz"]['Tam_Skor']
            en_cok_skor = gecerli_skorlar.value_counts().idxmax() if not gecerli_skorlar.empty else "-"
            gecerli_iyms = df[~df['IY_MS'].str.contains("Belirsiz")]['IY_MS']
            en_cok_iyms = gecerli_iyms.value_counts().idxmax() if not gecerli_iyms.empty else "-"
            
            mc1, mc2 = st.columns(2)
            mc1.metric("En Çok Tekrar Eden Skor", en_cok_skor)
            mc2.metric("En Çok Tekrar Eden İY/MS", en_cok_iyms)
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**📌 Maç Sonucu Dağılımı**")
                st.write(f"MS 1 : {df['MS_Sonuc'].value_counts().get('1', 0)} adet")
                st.write(f"MS 0 : {df['MS_Sonuc'].value_counts().get('0', 0)} adet")
                st.write(f"MS 2 : {df['MS_Sonuc'].value_counts().get('2', 0)} adet")
            with c2:
                st.markdown("**📌 Alt/Üst ve KG**")
                st.write(f"2.5 Üst : {ust} adet")
                st.write(f"2.5 Alt : {alt} adet")
                st.write(f"KG Var : {kg_var} adet")
                st.write(f"KG Yok : {kg_yok} adet")
            with c3:
                st.markdown("**📌 İY/MS Dağılımı**")
                for iyms_tipi, adet in df['IY_MS'].value_counts().items():
                    if "Belirsiz" not in iyms_tipi:
                        st.write(f"{iyms_tipi} : {adet} adet")

        with tab2:
            st.dataframe(df[['Lig', 'Tarih', 'Ev_Sahibi', 'Deplasman', 'Tam_Skor', 'IY_MS']], use_container_width=True)