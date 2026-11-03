# Proyek Analisis Data: Beijing Multi-Site Air Quality (PRSA)

Dashboard Streamlit untuk menjawab 3 pertanyaan bisnis tentang PM2.5 di 12 stasiun pemantauan Beijing (Maret 2013 - Februari 2017). Proses analisis lengkap ada di `notebook.ipynb`.

## Struktur Folder
```
submission
├── dashboard
│   ├── main_data.csv
│   └── dashboard.py
├── data
│   └── PRSA_Data_*.csv (12 file, satu per stasiun)
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment - Shell/Terminal (venv)
Disarankan Python 3.9 - 3.12. Jalankan perintah berikut dari folder `submission`.

**Windows**
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux**
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Setup Environment - Anaconda (alternatif)
```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Menjalankan Dashboard
Dari folder `submission` (environment sudah aktif):
```
streamlit run dashboard/dashboard.py
```
Dashboard akan terbuka di browser pada alamat `http://localhost:8501`.

## Menjalankan Notebook
Buka `notebook.ipynb` dari folder `submission` (agar folder `data/` terbaca), lalu jalankan semua sel. Notebook akan menghasilkan ulang `dashboard/main_data.csv`.
