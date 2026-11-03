import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.patches import Patch

st.set_page_config(page_title="Dashboard Kualitas Udara Beijing", page_icon="🌫️", layout="wide")
sns.set_theme(style="whitegrid")

NAAQS_HARIAN = 75
PERTANYAAN = {
    1: 'Stasiun mana yang memiliki rata-rata PM2.5 tertinggi dan terendah di antara 12 stasiun pemantauan di Beijing selama 1 Maret 2013 - 28 Februari 2017, dan berapa persentase hari dengan rata-rata PM2.5 harian di atas 75 µg/m³ (standar harian China) pada setiap stasiun, sehingga wilayah prioritas pengendalian polusi dapat ditentukan?',
    2: 'Pada bulan dan jam berapa rata-rata PM2.5 seluruh stasiun mencapai nilai tertinggi selama 1 Maret 2013 - 28 Februari 2017, dan berapa koefisien korelasi PM2.5 dengan kecepatan angin dan suhu, sehingga jadwal peringatan dini polusi dapat disusun?',
    3: 'Bagaimana perubahan rata-rata PM2.5 pada setiap stasiun untuk periode 12 bulan (Maret - Februari) dari 2013/2014 hingga 2016/2017, berapa persentase perubahannya, dan stasiun mana yang mengalami penurunan terbesar maupun terkecil, sehingga perkembangan kualitas udara di setiap stasiun dapat dievaluasi?',
}
NAMA_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    data = pd.read_csv(path, parse_dates=["datetime"])
    data["date"] = data["datetime"].dt.normalize()
    data["month"] = data["datetime"].dt.month
    data["hour"] = data["datetime"].dt.hour
    return data


df = load_data()

# ------------------------------------------------------------------ Sidebar
st.sidebar.title("🔎 Filter Data")
semua_stasiun = sorted(df["station"].unique())
stasiun_pilihan = st.sidebar.multiselect("Stasiun", semua_stasiun, default=semua_stasiun)

min_date, max_date = df["date"].min().date(), df["date"].max().date()
rentang = st.sidebar.date_input("Rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if len(rentang) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir pada sidebar.")
    st.stop()
if not stasiun_pilihan:
    st.warning("Pilih minimal satu stasiun pada sidebar.")
    st.stop()

mask = (
    df["station"].isin(stasiun_pilihan)
    & (df["date"] >= pd.Timestamp(rentang[0]))
    & (df["date"] <= pd.Timestamp(rentang[1]))
)
data = df[mask]
if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# ------------------------------------------------------------------ Header & metrik
st.title("🌫️ Dashboard Kualitas Udara Beijing (PM2.5)")
st.caption("Sumber data: Beijing Multi-Site Air Quality (12 stasiun, per jam, Maret 2013 - Februari 2017)")

harian = data.groupby(["station", "date"])["PM2.5"].mean().reset_index(name="pm25_harian")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rata-rata PM2.5", f"{data['PM2.5'].mean():.1f} µg/m³")
c2.metric("PM2.5 maksimum (per jam)", f"{data['PM2.5'].max():.0f} µg/m³")
c3.metric("% hari > 75 µg/m³", f"{(harian['pm25_harian'] > NAAQS_HARIAN).mean() * 100:.1f}%")
c4.metric("Jumlah stasiun", len(stasiun_pilihan))

tab1, tab2, tab3, tab4 = st.tabs(["📍 Pertanyaan 1: Per Stasiun", "🕒 Pertanyaan 2: Bulan, Jam & Cuaca", "📉 Pertanyaan 3: Tren Periode", "🔬 Analisis Lanjutan"])

# ------------------------------------------------------------------ Tab 1
with tab1:
    st.subheader("Pertanyaan 1")
    st.write(PERTANYAAN[1])
    ringkas = harian.groupby("station")["pm25_harian"].agg(rata_rata="mean").reset_index()
    ringkas["persen_hari_lebih_75"] = harian.groupby("station")["pm25_harian"].apply(
        lambda s: (s > NAAQS_HARIAN).mean() * 100
    ).values
    ringkas = ringkas.sort_values("rata_rata")

    fig, axes = plt.subplots(1, 2, figsize=(14, max(4, 0.45 * len(ringkas) + 2)))
    warna = ["#8ecae6"] * len(ringkas)
    if len(ringkas) > 1:
        warna[-1], warna[0] = "#d62828", "#2a9d8f"
    axes[0].barh(ringkas["station"], ringkas["rata_rata"], color=warna)
    axes[0].axvline(35, color="orange", linestyle="--", label="Standar tahunan China (35)")
    for i, v in enumerate(ringkas["rata_rata"]):
        axes[0].text(v + 0.5, i, f"{v:.1f}", va="center", fontsize=9)
    axes[0].set_title("Rata-rata PM2.5 per Stasiun")
    axes[0].set_xlabel("PM2.5 (µg/m³)")
    axes[0].set_xlim(0, ringkas["rata_rata"].max() * 1.12)
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False)

    r2 = ringkas.sort_values("persen_hari_lebih_75")
    axes[1].barh(r2["station"], r2["persen_hari_lebih_75"], color="#f4a261")
    for i, v in enumerate(r2["persen_hari_lebih_75"]):
        axes[1].text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=9)
    axes[1].set_title("% Hari PM2.5 Harian > 75 µg/m³")
    axes[1].set_xlabel("% hari")
    plt.tight_layout()
    st.pyplot(fig)

    tertinggi, terendah = ringkas.iloc[-1], ringkas.iloc[0]
    st.info(
        f"Tertinggi: **{tertinggi['station']}** ({tertinggi['rata_rata']:.1f} µg/m³), "
        f"terendah: **{terendah['station']}** ({terendah['rata_rata']:.1f} µg/m³) pada filter yang dipilih."
    )
    st.dataframe(
        ringkas.sort_values("rata_rata", ascending=False)
        .rename(columns={"station": "Stasiun", "rata_rata": "Rata-rata PM2.5", "persen_hari_lebih_75": "% hari > 75"})
        .round(2),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Kesimpulan")
    st.write(
        "Dongsi adalah stasiun dengan rata-rata PM2.5 tertinggi (85,9 µg/m³; 43,3% harinya > 75 µg/m³) "
        "dan Dingling terendah (66,2 µg/m³; 31,8% hari). Stasiun pusat kota konsisten lebih tercemar "
        "daripada stasiun pinggiran, tetapi seluruh stasiun masih jauh di atas standar WHO maupun China."
    )
    st.subheader("Rekomendasi")
    st.write(
        "Prioritaskan program pengendalian emisi (pembatasan kendaraan, pengawasan industri dan pembakaran) "
        "di wilayah pusat kota dengan PM2.5 tertinggi seperti Dongsi, Nongzhanguan, dan Wanshouxigong, "
        "karena sekitar 43% harinya melebihi 75 µg/m³."
    )

# ------------------------------------------------------------------ Tab 2
with tab2:
    st.subheader("Pertanyaan 2")
    st.write(PERTANYAAN[2])
    per_bulan = data.groupby("month")["PM2.5"].mean().reindex(range(1, 13))
    per_jam = data.groupby("hour")["PM2.5"].mean()

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    warna_b = ["#8ecae6"] * 12
    warna_b[int(np.nanargmax(per_bulan.values))] = "#d62828"
    warna_b[int(np.nanargmin(per_bulan.values))] = "#2a9d8f"
    axes[0].bar(NAMA_BULAN, per_bulan.values, color=warna_b)
    axes[0].set_title("Rata-rata PM2.5 per Bulan")
    axes[0].set_ylabel("PM2.5 (µg/m³)")
    axes[1].plot(per_jam.index, per_jam.values, marker="o", color="#264653")
    axes[1].set_xticks(range(0, 24, 2))
    axes[1].set_title("Rata-rata PM2.5 per Jam")
    axes[1].set_xlabel("Jam")
    plt.tight_layout()
    st.pyplot(fig)

    bulan_max = NAMA_BULAN[int(np.nanargmax(per_bulan.values))]
    st.info(f"Bulan tertinggi: **{bulan_max}** ({np.nanmax(per_bulan.values):.1f} µg/m³) | "
            f"Jam tertinggi: **{per_jam.idxmax():02d}.00** ({per_jam.max():.1f} µg/m³)")

    kolom_cuaca = ["TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    r_angin = data["PM2.5"].corr(data["WSPM"])
    r_suhu = data["PM2.5"].corr(data["TEMP"])
    st.info(f"Korelasi PM2.5 dengan kecepatan angin: **{r_angin:.2f}** | dengan suhu: **{r_suhu:.2f}**")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    sns.heatmap(data[["PM2.5"] + kolom_cuaca].corr(), annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax2)
    ax2.set_title("Korelasi PM2.5 dengan Cuaca")
    plt.tight_layout()
    st.pyplot(fig2)

    st.subheader("Kesimpulan")
    st.write(
        "PM2.5 tertinggi terjadi pada Desember (103,9 µg/m³) dan pada malam hari sekitar pukul 22.00 "
        "(88,9 µg/m³). Kecepatan angin berkorelasi negatif terhadap PM2.5 (r = -0,27) dan suhu juga "
        "negatif lemah (r = -0,13). Saat angin tenang PM2.5 rata-rata 101,8 vs 35,4 saat angin kencang."
    )
    st.subheader("Rekomendasi")
    st.write(
        "Siapkan sistem peringatan dini dan imbauan kesehatan (masker, kurangi aktivitas luar ruang) "
        "khusus Desember – Maret, di malam hari, dan saat angin tenang (≤ 1 m/s) yang bisa dipantau "
        "dari prakiraan cuaca."
    )

# ------------------------------------------------------------------ Tab 3
with tab3:
    st.subheader("Pertanyaan 3")
    st.write(PERTANYAAN[3])
    st.caption("Periode = 12 bulan Maret - Februari agar perbandingan antartahun adil.")
    per_periode = data.groupby("periode")["PM2.5"].mean()
    tren = data.pivot_table(index="station", columns="periode", values="PM2.5", aggfunc="mean")

    punya_perubahan = tren.shape[1] >= 2
    if punya_perubahan:
        perubahan = ((tren.iloc[:, -1] - tren.iloc[:, 0]) / tren.iloc[:, 0] * 100).sort_values(ascending=False)
        turun_terbesar, turun_terkecil = perubahan.idxmin(), perubahan.idxmax()
    else:
        perubahan, turun_terbesar, turun_terkecil = None, None, None

    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    ax1.bar(per_periode.index, per_periode.values, color="#e9c46a")
    for i, v in enumerate(per_periode.values):
        ax1.text(i, v + 1, f"{v:.1f}", ha="center")
    ax1.set_title("Rata-rata PM2.5 per Periode")
    ax1.set_ylabel("PM2.5 (µg/m³)")

    if punya_perubahan:
        warna_bar = ["#2a9d8f" if s == turun_terbesar else "#d62828" if s == turun_terkecil else "#8ecae6" for s in perubahan.index]
        ax2.barh(perubahan.index, perubahan.values, color=warna_bar)
        for i, v in enumerate(perubahan.values):
            ax2.text(v - 0.3, i, f"{v:.1f}%", va="center", ha="right", fontsize=9)
        ax2.set_xlim(min(perubahan.min(), 0) * 1.25 if perubahan.min() < 0 else perubahan.min() - 1,
                     max(perubahan.max(), 0) * 1.25 if perubahan.max() > 0 else 0)
        ax2.axvline(0, color="black", linewidth=0.8)
        ax2.set_title(f"Perubahan PM2.5: {tren.columns[0]} ke {tren.columns[-1]} (%)")
        ax2.set_xlabel("Perubahan (%)")
        ax2.legend(handles=[Patch(color="#2a9d8f", label=f"Perubahan paling rendah: {turun_terbesar}"),
                            Patch(color="#d62828", label=f"Perubahan paling tinggi: {turun_terkecil}")],
                   loc="lower left", fontsize=9)
    else:
        ax2.axis("off")
        ax2.text(0.5, 0.5, "Pilih rentang tanggal yang mencakup\nminimal 2 periode untuk melihat perubahan",
                 ha="center", va="center")

    paleta = sns.color_palette("husl", len(tren))
    marker_garis = ["o", "s", "^", "D", "v", "P", "X", "*", "<", ">", "h", "p"]
    for i, stasiun in enumerate(tren.index):
        tebal = 3.2 if stasiun in (turun_terbesar, turun_terkecil) else 1.6
        ax3.plot(tren.columns, tren.loc[stasiun], marker=marker_garis[i % len(marker_garis)],
                 color=paleta[(i * 5) % len(tren)], linewidth=tebal, label=stasiun)
    ax3.set_title("Tren PM2.5 per Stasiun (garis tebal = perubahan terbesar dan terkecil)")
    ax3.set_ylabel("PM2.5 (µg/m³)")
    ax3.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9, frameon=False)
    plt.tight_layout()
    st.pyplot(fig)

    if punya_perubahan:
        st.info(f"Penurunan terbesar: **{turun_terbesar}** ({perubahan.min():.1f}%) | "
                f"penurunan terkecil: **{turun_terkecil}** ({perubahan.max():.1f}%)")

    if tren.shape[1] >= 2:
        tren["Perubahan (%)"] = (tren.iloc[:, -1] - tren.iloc[:, 0]) / tren.iloc[:, 0] * 100
        st.dataframe(tren.sort_values("Perubahan (%)").round(2), use_container_width=True)
        st.caption("Perubahan (%) = periode terakhir terhadap periode pertama pada rentang tanggal yang dipilih. "
                   "Jika rentang tanggal tidak mencakup periode penuh, perbandingan bisa tidak adil.")

    st.subheader("Kesimpulan")
    st.write(
        "Rata-rata PM2.5 seluruh stasiun turun 16,2% dari 2013/2014 (86,95) ke 2015/2016 (72,89), "
        "namun naik 6,8% di 2016/2017 (77,87); secara keseluruhan turun 10,4%. Semua stasiun membaik "
        "antara 5,8% (Gucheng) hingga 21,1% (Wanliu), tetapi perbaikan belum stabil."
    )
    st.subheader("Rekomendasi")
    st.write(
        "Selidiki penyebab kenaikan PM2.5 di periode 2016/2017 dan pelajari praktik di Wanliu yang "
        "membaik paling besar untuk direplikasi di stasiun yang perbaikannya kecil seperti Gucheng, "
        "Guanyuan, dan Dongsi."
    )
    st.caption(
        "Catatan keterbatasan: analisis ini hanya memakai data 12 stasiun periode 2013–2017, "
        "sehingga perlu data terbaru untuk memastikan tren saat ini."
    )

# ------------------------------------------------------------------ Tab 4
with tab4:
    st.subheader("Analisis Lanjutan")
    st.write("Binning (pengelompokan manual) kategori kualitas udara & kecepatan angin.")

    batas_kategori = [0, 35, 75, 115, 150, 250, np.inf]
    label_kategori = ["Baik (0-35)", "Sedang (35-75)", "Tidak sehat sensitif (75-115)",
                      "Tidak sehat (115-150)", "Sangat tidak sehat (150-250)", "Berbahaya (>250)"]
    data_lanjutan = data.copy()
    data_lanjutan["kategori_pm25"] = pd.cut(data_lanjutan["PM2.5"], bins=batas_kategori,
                                            labels=label_kategori, include_lowest=True)
    data_lanjutan["kelas_angin"] = pd.cut(data_lanjutan["WSPM"], bins=[-0.01, 1, 2, 3, np.inf],
                                          labels=["Tenang (<=1 m/s)", "Lemah (1-2)", "Sedang (2-3)", "Kencang (>3)"])

    fig, axes = plt.subplots(1, 2, figsize=(17, 6))

    dist = (data_lanjutan["kategori_pm25"].value_counts(normalize=True).reindex(label_kategori) * 100)
    axes[0].barh(dist.index[::-1], dist.values[::-1], color=sns.color_palette("RdYlGn_r", 6)[::-1])
    for i, v in enumerate(dist.values[::-1]):
        axes[0].text(v + 0.3, i, f"{v:.1f}%", va="center")
    axes[0].set_title("Distribusi Jam-Pengamatan per Kategori PM2.5")
    axes[0].set_xlabel("% jam")

    angin_lanjutan = data_lanjutan.groupby("kelas_angin", observed=False)["PM2.5"].mean()
    axes[1].bar(angin_lanjutan.index.astype(str), angin_lanjutan.values, color="#457b9d")
    for i, v in enumerate(angin_lanjutan.values):
        axes[1].text(i, v + 1, f"{v:.1f}", ha="center")
    axes[1].set_title("Rata-rata PM2.5 menurut Kelas Kecepatan Angin")
    axes[1].set_ylabel("PM2.5 (µg/m³)")

    plt.tight_layout()
    st.pyplot(fig)

    persen_buruk = round(dist.iloc[-2:].sum(), 2)
    st.info(f"Persentase jam pada kategori 'Sangat tidak sehat' ke atas: **{persen_buruk}%**")
    st.write("Rata-rata PM2.5 menurut kelas angin:")
    st.dataframe(
        angin_lanjutan.reset_index().rename(columns={"kelas_angin": "Kelas Angin", "PM2.5": "Rata-rata PM2.5 (µg/m³)"}).round(1),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")
st.caption("Proyek Analisis Data - Dicoding")
