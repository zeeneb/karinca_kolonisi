# Karınca Kolonisi Optimizasyonu (ACO) ile Gezgin Satıcı Problemi (TSP) Simülatörü

Bu proje, **Karınca Kolonisi Optimizasyonu (Ant Colony Optimization - ACO)** algoritmasının Gezgin Satıcı Problemi (Traveling Salesperson Problem - TSP) üzerindeki adım adım çalışma mantığını görselleştiren, Python ve Tkinter ile geliştirilmiş bir eğitim aracıdır.

---

## 📌 Proje Özellikleri

- **Saf Python:** `numpy`, `scipy` veya `matplotlib` gibi harici kütüphanelere ihtiyaç duymaz. Yalnızca Python standart kütüphaneleri (`tkinter`, `math`, `random`) kullanılmıştır.
- **Adım Adım Çalışma (Step-by-Step):** Algoritma tek bir döngüde bitip sonucu gizlemez; her **"1 İterasyon İlerle"** butonuna basıldığında tam 1 tur çalışır ve ara durumları gösterir.
- **Görsel Canvas Haritası:** 5 şehrin (A, B, C, D, E) konumlarını ve karıncaların bulduğu en iyi rotayı (Global Best) renkli çizgilerle dinamik olarak çizer.
- **Detaylı Simülasyon Günlüğü:** Her iterasyonda hangi karıncanın hangi rotayı gezdiği, toplam tur mesafesi, turun en iyisi ve genel en iyi rota anlık olarak metin kutusuna yazdırılır.
- **Dinamik Parametre Girişi:** Kullanıcı arayüz üzerinden tüm hiperparametreleri değiştirebilir.

---

## 🧮 Algoritma ve Matematiksel Temeller

### 1. Sezgisel Bilgi / Görünürlük (Heuristic Information - $\eta$)
Şehir $i$ ile şehir $j$ arasındaki Öklid mesafesi $d_{ij}$ olmak üzere, yakın şehirlerin daha cazip olması için görünürlük şu şekilde tanımlanır:
$$\eta_{ij} = \frac{1}{d_{ij}}$$

### 2. Şehir Seçim Olasılığı (Rulet Tekerleği Kuralı)
Karınca mevcut $i$ şehrindeyken henüz ziyaret etmediği bir $j$ şehrine geçme olasılığı:
$$P_{ij} = \frac{[\tau_{ij}]^\alpha \cdot [\eta_{ij}]^\beta}{\sum_{k \in \text{ziyaret edilmemiş}} [\tau_{ik}]^\alpha \cdot [\eta_{ik}]^\beta}$$

- $\tau_{ij}$: $i$ ve $j$ şehirleri arasındaki feromon miktarı
- $\eta_{ij}$: Görünürlük katsayısı ($1 / d_{ij}$)
- $\alpha$ (Alfa): Feromonun önem derecesi
- $\beta$ (Beta): Mesafenin / sezgisel bilginin önem derecesi

### 3. Feromon Buharlaşması (Evaporation)
Eski yolların etkisini zamanla azaltmak ve yerel minimumlara takılmamak için feromonlar buharlaşır:
$$\tau_{ij} \leftarrow (1 - \rho) \cdot \tau_{ij}$$
- $\rho$ (Rho): Buharlaşma katsayısı ($0 \le \rho < 1$)

### 4. Feromon Güncellemesi (Pheromone Deposit)
Turunu tamamlayan $k$. karınca gezdiği kenarlara mesafesiyle ters orantılı olarak feromon bırakır:
$$\Delta \tau_{ij}^k = \frac{Q}{L_k}$$
$$\tau_{ij} \leftarrow \tau_{ij} + \sum_{k} \Delta \tau_{ij}^k$$
- $L_k$: $k$. karıncanın tamamladığı toplam tur uzunluğu
- $Q$: Feromon sabit katsayısı

---

## 🚀 Nasıl Çalıştırılır?

Terminal veya Komut İstemi (CMD / PowerShell) üzerinden şu komut ile çalıştırabilirsiniz:

```bash
python karinca_kolonisi_tsp.py
```
*(Windows sistemlerde Python sürümüne göre `py karinca_kolonisi_tsp.py` şeklinde de çalıştırılabilir.)*

---

## 🎮 Arayüz Kullanımı

1. **Parametreleri Ayarlayın:**
   - **Karınca Sayısı:** Kolonideki karınca adedi (Örn: 4 veya 5)
   - **Buharlaşma Oranı ($\rho$):** Örn: 0.1
   - **Feromon Katsayısı ($\alpha$):** Örn: 1.0
   - **Görünürlük Katsayısı ($\beta$):** Örn: 2.0
   - **Başlangıç Feromonu ($\tau_0$):** Örn: 1.0
2. **"▶ 1 İterasyon İlerle":** Her tıklamada 1 iterasyon hesaplanır, sonuçlar log ekranında ve canvas haritasında anında güncellenir.
3. **"⏩ Otomatik Başlat":** Sürekli adımlama moduna geçer (istediğiniz zaman duraklatabilirsiniz).
4. **"🔄 Simülasyonu Sıfırla":** Koloniyi 0. iterasyona ve başlangıç feromon değerlerine geri döndürür.
