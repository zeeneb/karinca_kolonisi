"""
=============================================================================
KARINCA KOLONİSİ OPTİMİZASYONU (ACO - ANT COLONY OPTIMIZATION)
GEZGİN SATICI PROBLEMİ (TSP) SİMÜLASYONU

Ders / Seviye: Üniversite Lisans Düzeyi
Kullanılan Kütüphaneler: tkinter, math, random (Harici kütüphane gerektirmez)
=============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
import random


class KarincaKolonisiSimulasyonu:
    def __init__(self, pencere):
        self.pencere = pencere
        self.pencere.title("Karınca Kolonisi Optimizasyonu (KKO / ACO) - TSP Simülasyonu")
        self.pencere.geometry("1100x750")
        self.pencere.minsize(1000, 700)
        self.pencere.configure(bg="#f1f5f9")

        # -------------------------------------------------------------
        # 1. PROBLEM TANIMI: ŞEHİRLER VE KOORDİNATLARI
        # -------------------------------------------------------------
        # Basit ve anlaşılır olması için 5 adet şehir tanımlıyoruz.
        # Bu koordinatlar canvas üzerinde çizilecek ve mesafeler Öklid bağıntısıyla hesaplanacaktır.
        self.sehirler = {
            "A": (120, 110),
            "B": (380, 90),
            "C": (420, 290),
            "D": (250, 390),
            "E": (90, 270)
        }
        self.sehir_isimleri = list(self.sehirler.keys())
        self.sehir_sayisi = len(self.sehir_isimleri)

        # Mesafe matrisi ve görünürlük (sezgisel bilgi: eta = 1 / mesafe) matrisi
        self.mesafe_matrisi = {}
        self.gorunurluk_matrisi = {}
        self._mesafeleri_hesapla()

        # -------------------------------------------------------------
        # 2. SİMÜLASYON DURUM DEĞİŞKENLERİ
        # -------------------------------------------------------------
        self.iterasyon = 0
        self.feromon_matrisi = {}
        self.genel_en_iyi_rota = None
        self.genel_en_iyi_mesafe = float('inf')
        self.son_tur_en_iyi_rota = None
        self.son_tur_en_iyi_mesafe = float('inf')

        # Otomatik çalıştırma (play/pause) durumu
        self.otomatik_calisiyor = False
        self.otomatik_islem_id = None

        # Sabit feromon katkı sabiti (Q)
        self.Q = 100.0

        # Arayüzü oluştur
        self._arayuz_bilesenlerini_olustur()

        # Simülasyonu başlangıç durumuna getir
        self.simulasyonu_sifirla()

    # =========================================================================
    # MATEMATİKSEL VE PROBLEM TEMEL FONKSİYONLARI
    # =========================================================================

    def _mesafeleri_hesapla(self):
        """
        Şehirler arasındaki Öklid mesafelerini ve görünürlük (eta = 1 / d)
        değerlerini hesaplar ve sözlükte saklar.
        """
        for s1 in self.sehir_isimleri:
            self.mesafe_matrisi[s1] = {}
            self.gorunurluk_matrisi[s1] = {}
            x1, y1 = self.sehirler[s1]

            for s2 in self.sehir_isimleri:
                if s1 == s2:
                    self.mesafe_matrisi[s1][s2] = 0.0
                    self.gorunurluk_matrisi[s1][s2] = 0.0
                else:
                    x2, y2 = self.sehirler[s2]
                    # İki nokta arası Öklid mesafesi formülü: sqrt((x2-x1)^2 + (y2-y1)^2)
                    mesafe = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                    self.mesafe_matrisi[s1][s2] = mesafe
                    # Görünürlük (Sezgisel Değer - eta): Şehir ne kadar yakınsa o kadar caziptir.
                    self.gorunurluk_matrisi[s1][s2] = 1.0 / mesafe

    def _feromon_matrisini_baslat(self, baslangic_feromon):
        """
        Her şehir çifti arasındaki feromon miktarını başlangıç değerine eşitler.
        """
        self.feromon_matrisi = {}
        for s1 in self.sehir_isimleri:
            self.feromon_matrisi[s1] = {}
            for s2 in self.sehir_isimleri:
                if s1 == s2:
                    self.feromon_matrisi[s1][s2] = 0.0
                else:
                    self.feromon_matrisi[s1][s2] = baslangic_feromon

    def _rota_mesafesi_hesapla(self, rota):
        """
        Verilen bir turun toplam mesafesini hesaplar (başlangıç şehrine dönüş dahil).
        Örnek rota: ['A', 'C', 'B', 'D', 'E', 'A']
        """
        toplam_mesafe = 0.0
        for i in range(len(rota) - 1):
            s1 = rota[i]
            s2 = rota[i + 1]
            toplam_mesafe += self.mesafe_matrisi[s1][s2]
        return toplam_mesafe

    # =========================================================================
    # KARINCA KOLONİSİ ADIM ADIM İŞLEYİŞİ
    # =========================================================================

    def tek_karinca_tur_olustur(self, alfa, beta):
        """
        Tek bir karınca için olasılıksal kuralla tam bir TSP turu oluşturur.
        Olasılık Formülü:
          P(i -> j) = (tau[i][j]^alfa * eta[i][j]^beta) / TOPLAM(...)
        """
        # Karınca rastgele bir başlangıç şehrinden başlar
        baslangic_sehri = random.choice(self.sehir_isimleri)
        mevcut_sehir = baslangic_sehri

        ziyaret_edilenler = [mevcut_sehir]
        ziyaret_edilecekler = [s for s in self.sehir_isimleri if s != mevcut_sehir]

        # Bütün şehirler gezilene kadar ilerle
        while ziyaret_edilecekler:
            gecis_olasilik_paylari = []

            for hedef_sehir in ziyaret_edilecekler:
                # tau: Feromon miktarı
                tau = self.feromon_matrisi[mevcut_sehir][hedef_sehir]
                # eta: Görünürlük (1 / mesafe)
                eta = self.gorunurluk_matrisi[mevcut_sehir][hedef_sehir]

                # Olasılık formülünün pay kısmı: (tau^alfa) * (eta^beta)
                pay = (tau ** alfa) * (eta ** beta)
                gecis_olasilik_paylari.append(pay)

            toplam_pay = sum(gecis_olasilik_paylari)

            # Rulet tekerleği mantığıyla bir sonraki şehri seç
            if toplam_pay > 0:
                secim_olasiliklari = [p / toplam_pay for p in gecis_olasilik_paylari]
                sonraki_sehir = random.choices(ziyaret_edilecekler, weights=secim_olasiliklari, k=1)[0]
            else:
                # Olasılıklar sıfır ise rastgele bir şehir seçilir
                sonraki_sehir = random.choice(ziyaret_edilecekler)

            ziyaret_edilenler.append(sonraki_sehir)
            ziyaret_edilecekler.remove(sonraki_sehir)
            mevcut_sehir = sonraki_sehir

        # Turu tamamlamak için başlangıç şehrine geri dönülür
        ziyaret_edilenler.append(baslangic_sehri)
        return ziyaret_edilenler

    def bir_iterasyon_ilerle(self):
        """
        '1 İterasyon İlerle' butonunun tetiklediği ana simülasyon fonksiyonudur:
        1. Parametreleri arayüzden okur.
        2. Her karınca için bir rota oluşturur ve mesafesini hesaplar.
        3. Bu turdaki ve genel en iyi rotaları günceller.
        4. Feromon buharlaşmasını uygular: tau = (1 - rho) * tau
        5. Karıncaların rotalarına göre feromon güncellemesi yapar: delta_tau = Q / L
        6. Arayüzü (Text log ve Canvas) günceller.
        """
        # 1. Parametreleri oku
        try:
            karinca_sayisi = int(self.entry_karinca.get().strip())
            rho = float(self.entry_rho.get().strip())
            alfa = float(self.entry_alfa.get().strip())
            beta = float(self.entry_beta.get().strip())

            if karinca_sayisi <= 0:
                raise ValueError("Karınca sayısı 1 veya daha büyük olmalıdır.")
            if not (0.0 <= rho < 1.0):
                raise ValueError("Buharlaşma oranı (rho) 0 ile 1 arasında olmalıdır.")
        except ValueError as e:
            messagebox.showerror("Geçersiz Parametre", f"Lütfen geçerli sayısal değerler girin!\nHata: {e}")
            self.otomatik_calismayi_durdur()
            return

        self.iterasyon += 1

        # 2. Bütün karıncaların rotalarını oluştur
        karinca_rotalari = []
        tur_en_iyi_rota = None
        tur_en_iyi_mesafe = float('inf')

        for k_idx in range(karinca_sayisi):
            rota = self.tek_karinca_tur_olustur(alfa=alfa, beta=beta)
            mesafe = self._rota_mesafesi_hesapla(rota)
            karinca_rotalari.append((k_idx + 1, rota, mesafe))

            # Tur içindeki en iyi rotayı kontrol et
            if mesafe < tur_en_iyi_mesafe:
                tur_en_iyi_mesafe = mesafe
                tur_en_iyi_rota = rota

        self.son_tur_en_iyi_rota = tur_en_iyi_rota
        self.son_tur_en_iyi_mesafe = tur_en_iyi_mesafe

        # Genel en iyi rotayı kontrol et (Global Best)
        if tur_en_iyi_mesafe < self.genel_en_iyi_mesafe:
            self.genel_en_iyi_mesafe = tur_en_iyi_mesafe
            self.genel_en_iyi_rota = tur_en_iyi_rota

        # 3. Feromon Güncellemesi:
        # A) Buharlaşma (Evaporation): tau = (1 - rho) * tau
        for s1 in self.sehir_isimleri:
            for s2 in self.sehir_isimleri:
                if s1 != s2:
                    self.feromon_matrisi[s1][s2] = (1.0 - rho) * self.feromon_matrisi[s1][s2]
                    # Aşırı küçük değerlere düşmemesi için taban sınır
                    if self.feromon_matrisi[s1][s2] < 1e-4:
                        self.feromon_matrisi[s1][s2] = 1e-4

        # B) Karıncaların Feromon Bırakması (Deposit):
        # Her karınca gezdiği kenarlara delta_tau = Q / L kadar feromon bırakır
        for _, rota, mesafe in karinca_rotalari:
            delta_tau = self.Q / mesafe
            for i in range(len(rota) - 1):
                u = rota[i]
                v = rota[i + 1]
                self.feromon_matrisi[u][v] += delta_tau
                self.feromon_matrisi[v][u] += delta_tau

        # 4. Sonuçları Arayüze Yazdır ve Çiz
        self._log_ekle(self.iterasyon, karinca_rotalari, tur_en_iyi_rota, tur_en_iyi_mesafe)
        self._bilgi_kartini_guncelle()
        self._haritayi_ciz()

    def simulasyonu_sifirla(self):
        """
        Simülasyonu ilk ayarlara ve 0. iterasyona döndürür.
        """
        self.otomatik_calismayi_durdur()

        try:
            baslangic_feromon = float(self.entry_tau0.get().strip())
            if baslangic_feromon <= 0:
                raise ValueError("Başlangıç feromon değeri 0'dan büyük olmalıdır.")
        except (ValueError, AttributeError):
            baslangic_feromon = 1.0

        self.iterasyon = 0
        self.genel_en_iyi_rota = None
        self.genel_en_iyi_mesafe = float('inf')
        self.son_tur_en_iyi_rota = None
        self.son_tur_en_iyi_mesafe = float('inf')

        self._feromon_matrisini_baslat(baslangic_feromon)

        # Log alanını temizle ve karşılama mesajı yaz
        if hasattr(self, 'txt_log'):
            self.txt_log.config(state=tk.NORMAL)
            self.txt_log.delete("1.0", tk.END)
            self.txt_log.insert(tk.END, ">>> Karınca Kolonisi Optimizasyonu Simülasyonu Hazır.\n")
            self.txt_log.insert(tk.END, f">>> Tanımlı Şehirler: {', '.join(self.sehir_isimleri)} (Toplam {self.sehir_sayisi} Şehir)\n")
            self.txt_log.insert(tk.END, f">>> Başlangıç Feromon Değeri: {baslangic_feromon}\n")
            self.txt_log.insert(tk.END, ">>> Adım adım ilerlemek için '1 İterasyon İlerle' butonuna basınız.\n")
            self.txt_log.insert(tk.END, "=" * 65 + "\n\n")
            self.txt_log.config(state=tk.DISABLED)

        self._bilgi_kartini_guncelle()
        self._haritayi_ciz()

    def otomatik_calistir_degistir(self):
        """
        Otomatik adımlamayı başlatır veya duraklatır.
        """
        if self.otomatik_calisiyor:
            self.otomatik_calismayi_durdur()
        else:
            self.otomatik_calisiyor = True
            self.btn_otomatik.config(text="⏸ Duraklat", bg="#ea580c")
            self._otomatik_dongu()

    def _otomatik_dongu(self):
        if self.otomatik_calisiyor:
            self.bir_iterasyon_ilerle()
            # 600 milisaniye sonra bir sonraki iterasyonu çağır
            self.otomatik_islem_id = self.pencere.after(600, self._otomatik_dongu)

    def otomatik_calismayi_durdur(self):
        self.otomatik_calisiyor = False
        if hasattr(self, 'btn_otomatik'):
            self.btn_otomatik.config(text="⏩ Otomatik Başlat", bg="#0284c7")
        if self.otomatik_islem_id:
            self.pencere.after_cancel(self.otomatik_islem_id)
            self.otomatik_islem_id = None

    # =========================================================================
    # GÖRSELLEŞTİRME VE ÇİZİM METOTLARI (CANVAS)
    # =========================================================================

    def _haritayi_ciz(self):
        """
        Canvas bileşeni üzerinde:
        1. Tüm şehirler arası olası yolları (feromon yoğunluğuna göre kalınlık/renk) çizer.
        2. Son turun en iyi rotasını (kesikli turuncu çizgi) çizer.
        3. Genel en iyi rotayı (Global Best - kalın yeşil çizgi) çizer.
        4. Şehirleri daire ve isim etiketleriyle çizer.
        """
        self.canvas.delete("all")

        # 1. Şehirler arası olası bağlantıları çiz (Açık gri)
        for i, s1 in enumerate(self.sehir_isimleri):
            x1, y1 = self.sehirler[s1]
            for j, s2 in enumerate(self.sehir_isimleri):
                if i < j:
                    x2, y2 = self.sehirler[s2]
                    self.canvas.create_line(x1, y1, x2, y2, fill="#e2e8f0", width=1)

        # 2. Son turun en iyi rotasını çiz (Turuncu kesikli çizgi)
        if self.son_tur_en_iyi_rota and len(self.son_tur_en_iyi_rota) > 1:
            for i in range(len(self.son_tur_en_iyi_rota) - 1):
                s1 = self.son_tur_en_iyi_rota[i]
                s2 = self.son_tur_en_iyi_rota[i + 1]
                x1, y1 = self.sehirler[s1]
                x2, y2 = self.sehirler[s2]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#fb923c",
                    width=2,
                    dash=(4, 3)
                )

        # 3. Genel en iyi rotayı çiz (Global Best - Kalın Yeşil Çizgi)
        if self.genel_en_iyi_rota and len(self.genel_en_iyi_rota) > 1:
            for i in range(len(self.genel_en_iyi_rota) - 1):
                s1 = self.genel_en_iyi_rota[i]
                s2 = self.genel_en_iyi_rota[i + 1]
                x1, y1 = self.sehirler[s1]
                x2, y2 = self.sehirler[s2]
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#16a34a",
                    width=3.5,
                    capstyle=tk.ROUND
                )

        # 4. Şehirleri çiz (Renkli daireler ve harf etiketleri)
        r = 16  # Şehir dairesi yarıçapı
        for sehir, (x, y) in self.sehirler.items():
            # Gölge efekti
            self.canvas.create_oval(x - r + 2, y - r + 2, x + r + 2, y + r + 2, fill="#cbd5e1", outline="")
            # Şehir noktası
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#1e293b", outline="#3b82f6", width=2.5)
            # Şehir harfi
            self.canvas.create_text(x, y, text=sehir, fill="#ffffff", font=("Segoe UI", 11, "bold"))
            # Koordinat etiketi
            self.canvas.create_text(x, y + r + 11, text=f"({x}, {y})", fill="#64748b", font=("Segoe UI", 8))

    # =========================================================================
    # METİN GÜNLÜĞÜ VE BİLGİ GÜNCELLEMELERİ
    # =========================================================================

    def _log_ekle(self, iterasyon_no, karinca_rotalari, tur_en_iyi_rota, tur_en_iyi_mesafe):
        """
        Text kutusuna adım detaylarını yazar.
        """
        self.txt_log.config(state=tk.NORMAL)

        # Başlık
        self.txt_log.insert(tk.END, f"╔══════ İTERASYON {iterasyon_no} ══════╗\n", "iter_baslik")

        # Her karıncanın gezdiği rota ve mesafesi
        for k_no, rota, mesafe in karinca_rotalari:
            rota_metni = " -> ".join(rota)
            self.txt_log.insert(
                tk.END,
                f"  🐜 Karınca {k_no:02d}: {rota_metni} | Mesafe: {mesafe:.2f}\n"
            )

        # Bu turun en iyisi
        tur_rota_str = " -> ".join(tur_en_iyi_rota)
        self.txt_log.insert(
            tk.END,
            f"  ⚡ Bu Turun En İyisi : {tur_rota_str} (Mesafe: {tur_en_iyi_mesafe:.2f})\n",
            "tur_en_iyi"
        )

        # Genel en iyi rota
        genel_rota_str = " -> ".join(self.genel_en_iyi_rota)
        self.txt_log.insert(
            tk.END,
            f"  🏆 GENEL EN İYİ ROTA: {genel_rota_str} (Mesafe: {self.genel_en_iyi_mesafe:.2f})\n",
            "genel_en_iyi"
        )
        self.txt_log.insert(tk.END, "╚" + "═" * 40 + "╝\n\n")

        # Otomatik olarak en alt satıra kaydır
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _bilgi_kartini_guncelle(self):
        """
        Sağ alt köşedeki veya kontrol panelindeki özet sayaçlarını günceller.
        """
        self.lbl_ozet_iterasyon.config(text=f"İterasyon: {self.iterasyon}")

        if self.genel_en_iyi_rota is not None:
            self.lbl_ozet_mesafe.config(text=f"En İyi Mesafe: {self.genel_en_iyi_mesafe:.2f} px")
            self.lbl_ozet_rota.config(text=f"En İyi Rota: {' -> '.join(self.genel_en_iyi_rota)}")
        else:
            self.lbl_ozet_mesafe.config(text="En İyi Mesafe: -")
            self.lbl_ozet_rota.config(text="En İyi Rota: -")

    # =========================================================================
    # ARAYÜZ (GUI) BİLEŞENLERİ TASARIMI
    # =========================================================================

    def _arayuz_bilesenlerini_olustur(self):
        # Üst Başlık Banner
        header_frame = tk.Frame(self.pencere, bg="#1e293b", height=50)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="🐜 Karınca Kolonisi Optimizasyonu (KKO / ACO) Simülatörü",
            font=("Segoe UI", 14, "bold"),
            bg="#1e293b",
            fg="#f8fafc",
            padx=15,
            pady=10
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Gezgin Satıcı Problemi (TSP) Çözümü",
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#94a3b8",
            padx=10
        )
        subtitle_lbl.pack(side=tk.RIGHT)

        # Ana içerik gövdesi (Sol: Kontroller, Sağ: Çizim ve Günlük)
        main_content = tk.Frame(self.pencere, bg="#f1f5f9", padx=12, pady=10)
        main_content.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # SOL PANEL: Parametreler, Butonlar ve Şehir Tablosu
        # -------------------------------------------------------------
        sol_panel = tk.Frame(main_content, bg="#f1f5f9", width=340)
        sol_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sol_panel.pack_propagate(False)

        # PARAMETRELER KUTUSU
        param_frame = tk.LabelFrame(
            sol_panel,
            text=" ⚙ Simülasyon Parametreleri ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=12,
            pady=10,
            relief=tk.GROOVE
        )
        param_frame.pack(fill=tk.X, pady=(0, 10))

        # 1. Karınca Sayısı
        tk.Label(param_frame, text="Karınca Sayısı (m):", bg="#ffffff", anchor="w", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_karinca = tk.Entry(param_frame, width=8, justify="center", font=("Segoe UI", 9, "bold"))
        self.entry_karinca.insert(0, "4")
        self.entry_karinca.grid(row=0, column=1, sticky="e", pady=4)

        # 2. Buharlaşma Oranı (rho)
        tk.Label(param_frame, text="Buharlaşma Oranı (ρ):", bg="#ffffff", anchor="w", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_rho = tk.Entry(param_frame, width=8, justify="center", font=("Segoe UI", 9, "bold"))
        self.entry_rho.insert(0, "0.1")
        self.entry_rho.grid(row=1, column=1, sticky="e", pady=4)

        # 3. Feromon Etkisi (alfa)
        tk.Label(param_frame, text="Feromon Katsayısı (α):", bg="#ffffff", anchor="w", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_alfa = tk.Entry(param_frame, width=8, justify="center", font=("Segoe UI", 9, "bold"))
        self.entry_alfa.insert(0, "1.0")
        self.entry_alfa.grid(row=2, column=1, sticky="e", pady=4)

        # 4. Görünürlük Etkisi (beta)
        tk.Label(param_frame, text="Mesafe/Görünürlük (β):", bg="#ffffff", anchor="w", font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_beta = tk.Entry(param_frame, width=8, justify="center", font=("Segoe UI", 9, "bold"))
        self.entry_beta.insert(0, "2.0")
        self.entry_beta.grid(row=3, column=1, sticky="e", pady=4)

        # 5. Başlangıç Feromon Değeri (tau0)
        tk.Label(param_frame, text="Başlangıç Feromonu (τ₀):", bg="#ffffff", anchor="w", font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=4)
        self.entry_tau0 = tk.Entry(param_frame, width=8, justify="center", font=("Segoe UI", 9, "bold"))
        self.entry_tau0.insert(0, "1.0")
        self.entry_tau0.grid(row=4, column=1, sticky="e", pady=4)

        # BUTONLAR KUTUSU
        buton_frame = tk.LabelFrame(
            sol_panel,
            text=" 🎮 Kontrol Paneli ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=12,
            pady=10,
            relief=tk.GROOVE
        )
        buton_frame.pack(fill=tk.X, pady=(0, 10))

        # 1 İTERASYON İLERLE (Büyük Birincil Buton)
        self.btn_adim = tk.Button(
            buton_frame,
            text="▶  1 İterasyon İlerle",
            command=self.bir_iterasyon_ilerle,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            pady=7
        )
        self.btn_adim.pack(fill=tk.X, pady=(0, 6))

        # OTOMATİK ÇALIŞTIR / DURDUR
        self.btn_otomatik = tk.Button(
            buton_frame,
            text="⏩ Otomatik Başlat",
            command=self.otomatik_calistir_degistir,
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            pady=5
        )
        self.btn_otomatik.pack(fill=tk.X, pady=(0, 6))

        # SIFIRLA / YENİDEN BAŞLAT
        self.btn_sifirla = tk.Button(
            buton_frame,
            text="🔄 Simülasyonu Sıfırla",
            command=self.simulasyonu_sifirla,
            bg="#64748b",
            fg="#ffffff",
            activebackground="#475569",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            pady=5
        )
        self.btn_sifirla.pack(fill=tk.X)

        # ŞEHİR LİSTESİ BİLGİ KUTUSU
        sehir_frame = tk.LabelFrame(
            sol_panel,
            text=" 📍 Şehir Koordinatları ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=8,
            relief=tk.GROOVE
        )
        sehir_frame.pack(fill=tk.X, pady=(0, 10))

        for sehir, (x, y) in self.sehirler.items():
            row_f = tk.Frame(sehir_frame, bg="#ffffff")
            row_f.pack(fill=tk.X, pady=1)
            tk.Label(row_f, text=f"Şehir {sehir}:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#2563eb", width=8, anchor="w").pack(side=tk.LEFT)
            tk.Label(row_f, text=f"X = {x}, Y = {y}", font=("Consolas", 9), bg="#ffffff", fg="#475569").pack(side=tk.LEFT)

        # ÖZET DURUM KARTI (SOL ALT)
        ozet_frame = tk.Frame(sol_panel, bg="#0f172a", padx=12, pady=10)
        ozet_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_ozet_iterasyon = tk.Label(
            ozet_frame,
            text="İterasyon: 0",
            font=("Segoe UI", 10, "bold"),
            bg="#0f172a",
            fg="#38bdf8",
            anchor="w"
        )
        self.lbl_ozet_iterasyon.pack(fill=tk.X)

        self.lbl_ozet_mesafe = tk.Label(
            ozet_frame,
            text="En İyi Mesafe: -",
            font=("Segoe UI", 10, "bold"),
            bg="#0f172a",
            fg="#4ade80",
            anchor="w"
        )
        self.lbl_ozet_mesafe.pack(fill=tk.X, pady=2)

        self.lbl_ozet_rota = tk.Label(
            ozet_frame,
            text="En İyi Rota: -",
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg="#cbd5e1",
            anchor="w",
            wraplength=310
        )
        self.lbl_ozet_rota.pack(fill=tk.X)

        # -------------------------------------------------------------
        # SAĞ PANEL: Canvas (Harita) ve Metin Günlüğü (ScrolledText)
        # -------------------------------------------------------------
        sag_panel = tk.Frame(main_content, bg="#f1f5f9")
        sag_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ÜST: HARİTA VE LEJANT ÇERÇEVESİ
        canvas_container = tk.LabelFrame(
            sag_panel,
            text=" 🗺 Şehir Haritası ve Bulunan Rotalar ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=8,
            relief=tk.GROOVE
        )
        canvas_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas
        self.canvas = tk.Canvas(
            canvas_container,
            bg="#ffffff",
            height=370,
            highlightthickness=1,
            highlightbackground="#e2e8f0"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Lejant (Çizgi renklerinin anlamı)
        lejant_frame = tk.Frame(canvas_container, bg="#ffffff", pady=4)
        lejant_frame.pack(fill=tk.X)

        tk.Label(lejant_frame, text="■", fg="#16a34a", bg="#ffffff", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        tk.Label(lejant_frame, text="Genel En İyi Rota (Global Best)  ", bg="#ffffff", font=("Segoe UI", 8, "bold"), fg="#1e293b").pack(side=tk.LEFT)

        tk.Label(lejant_frame, text="■", fg="#fb923c", bg="#ffffff", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        tk.Label(lejant_frame, text="Son Turun En İyisi  ", bg="#ffffff", font=("Segoe UI", 8), fg="#475569").pack(side=tk.LEFT)

        tk.Label(lejant_frame, text="■", fg="#cbd5e1", bg="#ffffff", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        tk.Label(lejant_frame, text="Olası Yollar", bg="#ffffff", font=("Segoe UI", 8), fg="#94a3b8").pack(side=tk.LEFT)

        # ALT: SİMÜLASYON GÜNLÜĞÜ (ScrolledText)
        log_container = tk.LabelFrame(
            sag_panel,
            text=" 📋 Adım Adım Simülasyon Günlüğü (Detaylı Takip) ",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=6,
            relief=tk.GROOVE
        )
        log_container.pack(fill=tk.BOTH, expand=True)

        self.txt_log = scrolledtext.ScrolledText(
            log_container,
            wrap=tk.WORD,
            height=11,
            font=("Consolas", 9),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="#ffffff",
            relief=tk.FLAT
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        # Text renklendirme etiketleri (Tag styling)
        self.txt_log.tag_config("iter_baslik", foreground="#38bdf8", font=("Consolas", 9, "bold"))
        self.txt_log.tag_config("tur_en_iyi", foreground="#fb923c", font=("Consolas", 9, "bold"))
        self.txt_log.tag_config("genel_en_iyi", foreground="#4ade80", font=("Consolas", 9, "bold"))


# =============================================================================
# PROGRAM GİRİŞ NOKTASI (MAIN)
# =============================================================================
if __name__ == "__main__":
    kok_pencere = tk.Tk()
    uygulama = KarincaKolonisiSimulasyonu(kok_pencere)
    kok_pencere.mainloop()
