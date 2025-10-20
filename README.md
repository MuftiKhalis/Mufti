# Projects

## Nexus Calculator Vault

Sebuah kalkulator ilmiah modern dengan antarmuka adaptif, histori
perhitungan real-time, dan vault terenkripsi untuk menyimpan catatan
pribadi. Aplikasi ini dirancang untuk menjadi utilitas produktivitas dan
keamanan dalam satu dashboard.

### Menjalankan aplikasi

1. Pastikan Python 3.9 atau lebih baru tersedia.
2. Instal dependensi yang dibutuhkan:

   ```bash
   pip install flask cryptography
   ```

3. Jalankan server web dengan:

   ```bash
   python -m calculator_vault.app
   ```

4. Buka <http://127.0.0.1:5000/> di browser untuk mulai menggunakan
   kalkulator dan vault.

### Fitur utama

- **Kalkulator ilmiah adaptif** dengan dukungan fungsi trigonometri,
  eksponensial, memori pintar, dan dukungan keyboard.
- **Histori perhitungan real-time** yang dapat dikelola tanpa me-refresh
  halaman.
- **Vault terenkripsi** dengan password master, dukungan tambah/edit/
  hapus catatan secara langsung, serta indikator status yang jelas.
- **UI futuristik** dengan mode gelap, animasi halus, dan kompatibel di
  desktop maupun perangkat bergerak.

Data vault disimpan secara lokal pada `data/calculator_vault.sqlite`
dengan enkripsi simetris berbasis password master.

## Realtime Planner & Invoice Studio

Sebuah aplikasi web interaktif untuk merancang jadwal kegiatan,
mengelola rincian invoice secara realtime, dan menghasilkan QR code serta
dokumen PDF siap kirim.

### Menjalankan aplikasi

1. Pastikan Python 3.9 atau lebih baru tersedia.
2. Instal dependensi yang dibutuhkan:

   ```bash
   pip install -r requirements.txt
   ```

3. Jalankan server web dengan:

   ```bash
   python -m planner_invoice.app
   ```

4. Buka <http://127.0.0.1:5000/> di browser untuk mulai mengatur jadwal,
   membuat invoice, mengunduh PDF, atau mengekspor data mentah.

### Fitur utama

- **Manajemen jadwal realtime** dengan timeline yang selalu sinkron
  tanpa perlu me-refresh halaman.
- **Penyusunan invoice dinamis** lengkap dengan perhitungan diskon,
  pajak, dan total akhir.
- **Ekspor fleksibel** ke dalam format PDF maupun berkas JSON mentah.
- **QR code otomatis** yang merangkum detail invoice sehingga mudah
  dibagikan dan dipindai di perangkat seluler.

## Guess the Country

An interactive geography quiz that challenges you to identify countries
from their flags and trivia clues. The project ships with both a
terminal-based experience and a real-time web interface, each powered by
the shared dataset defined in
[`game/guess_the_country.py`](game/guess_the_country.py).

### Play in the Terminal

1. Ensure you have Python 3.9 or newer installed.
2. Clone this repository and open a terminal in the project root.
3. Run the game with:

   ```bash
   python -m game.guess_the_country
   ```

   Optional arguments:

   - `--rounds N` limits the session to `N` rounds (otherwise the game
     continues until you type `quit`).
   - `--seed SEED` sets a deterministic random seed, which is useful for
     demonstrations or testing.

Press `Ctrl+C`, type `quit`, or enter `exit` at any guess prompt to end
the session. After each round the game reports whether you guessed the
country correctly and keeps a running score.

### Play in the Browser

The web experience uses Flask to serve a single-page application with a
live scoreboard and dynamic clues. Install the runtime dependency and
launch the server with:

```bash
pip install flask
python -m game.guess_the_country --web
```

By default the game will be available at
<http://127.0.0.1:5000/> — open the URL in your browser to play. Each
guess is checked in real-time, the scoreboard updates immediately, and
you can reveal additional hints with a single click. Stop the server
with `Ctrl+C`.

### Extending the Dataset

Country data lives in the `COUNTRY_DATA` list within
[`game/guess_the_country.py`](game/guess_the_country.py). Each entry is a
`CountryClue` instance with a country name, flag emoji, and a collection
of textual hints.

To add more countries:

1. Open `game/guess_the_country.py`.
2. Append a new `CountryClue` to `COUNTRY_DATA`, providing:
   - `name`: The country's common name (e.g., `"Spain"`).
   - `flag`: A Unicode flag emoji or simple ASCII description.
   - `hints`: A tuple of one or more textual hints that become
     progressively more revealing.
3. Save the file and rerun the game.

The hints appear sequentially after each incorrect guess, so arrange
them from most cryptic to most informative to balance difficulty.

## Original Profile README

- 👋 Hi, I’m @MuftiKhalis
- 👀 I’m interested in tech
- 🌱 I’m currently learning biological sciences
- 💞️ I’m looking to collaborate on nothing
- 📫 How to reach me ...

<!---
MuftiKhalis/MuftiKhalis is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
-->
