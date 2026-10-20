import pandas as pd
import matplotlib.pyplot as plt


# 1. Veriyi okuma ve ilk inceleme
# Çalışma klasörü air-quality-intelligence olmalı; outputs klasörü bulunmalı.
file_path = "data/raw/PRSA_Data_Aotizhongxin_20130301-20170228.csv"
df = pd.read_csv(file_path)

print(df.head())
df.info()


# 2. Eksik değerler, tekrarlanan kayıtlar ve özet istatistikler
print("\nSütunlara göre eksik değer sayıları:")
print(df.isna().sum())

# Aynı istasyon ve aynı saate ait birden fazla kayıt olup olmadığını kontrol et.
included_columns = ["year", "month", "day", "hour", "station"]
print("\nAynı istasyon ve saate ait tekrarlanan kayıt sayısı:")
print(df[included_columns].duplicated().sum())

selected_columns = ["PM2.5", "PM10", "TEMP", "WSPM"]
print("\nSeçilen değişkenlerin özet istatistikleri:")
print(df[selected_columns].describe())

# Ham df tablosunu koru. Eksik değerleri doldurmak yerine her analiz için
# gerekli sütunlardaki mevcut ölçümleri kullan. Yüksek değerleri otomatik silme.


# 3. PM2.5 dağılımı
new_pm25 = df["PM2.5"].dropna()

plt.figure()
plt.hist(new_pm25)
plt.xlabel("PM2.5 (µg/m³)")
plt.ylabel("Ölçüm sayısı")
plt.title("Ölçümlerin Yoğunlaştığı Değerler")
plt.savefig("outputs/01_pm25_histogram.png", dpi=150, bbox_inches="tight")
plt.show()

plt.figure()
plt.boxplot(new_pm25)
plt.title("Aotizhongxin PM2.5")
plt.ylabel("PM2.5 (µg/m³)")
plt.savefig("outputs/02_pm25_boxplot.png", dpi=150, bbox_inches="tight")
plt.show()

# Gözlem: Ölçümler düşük değerlerde yoğunlaşıyor; yüksek değerler ortalamayı
# yukarı çekiyor. PM2.5 ortalaması medyanından daha yüksek.


# 4. Sıcaklık ve rüzgar ile ilişkiler
weather_data = df[["PM2.5", "TEMP", "WSPM"]]
# Üç değişkeni aynı ölçüm kayıtları üzerinden karşılaştır.
new_weather_data = weather_data.dropna()

print("\nHava değişkenleri: eksikler çıkarılmadan önce ve sonra tablo boyutu:")
print(weather_data.shape)
print(new_weather_data.shape)

plt.figure()
plt.scatter(new_weather_data["TEMP"], new_weather_data["PM2.5"])
plt.xlabel("TEMP (°C)")
plt.ylabel("PM2.5 (µg/m³)")
plt.title("Sıcaklık - PM2.5 İlişkisi")
plt.savefig("outputs/03_temperature_pm25_scatter.png", dpi=150, bbox_inches="tight")
plt.show()

plt.figure()
plt.scatter(new_weather_data["WSPM"], new_weather_data["PM2.5"])
plt.xlabel("WSPM (m/s)")
plt.ylabel("PM2.5 (µg/m³)")
plt.title("Rüzgar Hızı - PM2.5 İlişkisi")
plt.savefig("outputs/04_wind_pm25_scatter.png", dpi=150, bbox_inches="tight")
plt.show()

corr = new_weather_data[["TEMP", "PM2.5", "WSPM"]].corr()
print("\nSıcaklık, PM2.5 ve rüzgar hızı korelasyonları:")
print(corr)

plt.figure()
plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
plt.colorbar(label="Korelasyon")
plt.xticks(range(len(corr.columns)), corr.columns)
plt.yticks(range(len(corr.columns)), corr.columns)
plt.title("Korelasyon Matrisi")
plt.savefig("outputs/05_weather_correlation.png", dpi=150, bbox_inches="tight")
plt.show()


# Rüzgar eşikleri bu proje için seçilmiştir; resmi sınıflandırma değildir.
# Fonksiyon, WSPM eksikleri çıkarılmış olan new_weather_data üzerinde kullanılır.
def classify_wind(speed):
    if speed < 1:
        return "Düşük"
    elif 1 <= speed < 3:
        return "Orta"
    else:
        return "Yüksek"


new_weather_data["wind_group"] = new_weather_data["WSPM"].map(classify_wind)

wind_summary = new_weather_data.groupby("wind_group").agg(
    mean=("PM2.5", "mean"),
    median=("PM2.5", "median"),
    count=("PM2.5", "count")
)
print("\nRüzgar gruplarına göre PM2.5 özeti:")
print(wind_summary)

plt.figure()
plt.bar(wind_summary.index, wind_summary["mean"])
plt.xlabel("Rüzgar Grupları")
plt.ylabel("PM2.5 (µg/m³)")
plt.title("Her Rüzgar Grubunun Ortalama PM2.5 Değeri")
plt.savefig("outputs/06_wind_group_comparison.png", dpi=150, bbox_inches="tight")
plt.show()

# Gözlem: Rüzgar grubu yükseldikçe ortalama ve medyan PM2.5 azalıyor.
# Bu karşılaştırma tek başına neden-sonuç ilişkisini göstermez.


# 5. Aylık değişimler ve yılların karşılaştırılması
# Aylık PM2.5 analizi için ham df kullanılır; TEMP veya WSPM eksikleri yüzünden
# mevcut PM2.5 ölçümlerini bu analizden çıkarmaya gerek yoktur.
monthly_summary = df.groupby(["year", "month"], as_index=False).agg(
    mean=("PM2.5", "mean"),
    median=("PM2.5", "median"),
    valid_count=("PM2.5", "count"),
    entry_count=("No", "count")
)

# No sütunu eksiksiz olduğu için count, dosyada bulunan aylık kayıt sayısını verir.
# valid_count yalnızca PM2.5 değeri dolu olan kayıtları sayar.
monthly_summary["missing_count"] = (
    monthly_summary["entry_count"] - monthly_summary["valid_count"]
)
monthly_summary["missing_percentage"] = (
    monthly_summary["missing_count"] / monthly_summary["entry_count"] * 100
)

# Tarih metnini oluşturmadan önce sayısal yıl ve ay sütunlarıyla sırala.
monthly_summary = monthly_summary.sort_values(["year", "month"])
year_text = monthly_summary["year"].astype(str)
month_text = monthly_summary["month"].astype(str)
monthly_summary["period"] = year_text + "-" + month_text

print("\nAylık PM2.5 özeti (ilk beş ay):")
print(monthly_summary.head())

plt.figure()
plt.plot(monthly_summary["period"], monthly_summary["mean"])
# Tüm aylar çizilir; okunabilirlik için yalnızca altı ayda bir etiket gösterilir.
plt.xticks(
    range(0, len(monthly_summary), 6),
    monthly_summary["period"].iloc[::6],
    rotation=45
)
plt.xlabel("Yıl-Ay")
plt.ylabel("PM2.5 (µg/m³)")
plt.title("Aotizhongxin - Aylık Ortalama PM2.5")
plt.savefig("outputs/07_monthly_pm25.png", dpi=150, bbox_inches="tight")
plt.show()

# Tüm yıllardaki aynı ayın mevcut saatlik ölçümlerini birlikte değerlendir.
month_comparison = df.groupby("month", as_index=False).agg(
    mean=("PM2.5", "mean"),
    median=("PM2.5", "median"),
    count=("PM2.5", "count")
)

plt.figure()
plt.bar(month_comparison["month"], month_comparison["mean"])
plt.xticks(month_comparison["month"])
plt.xlabel("Aylar")
plt.ylabel("PM2.5 (µg/m³) Ortalamaları")
plt.title("Aotizhongxin — Tüm Yıllar Birlikte Aylık PM2.5 Ortalamaları")
plt.savefig("outputs/08_calendar_month_comparison.png", dpi=150, bbox_inches="tight")
plt.show()

ranked_months = monthly_summary[
    ["period", "mean", "median", "missing_percentage"]
].sort_values("mean", ascending=False)

print("\nPM2.5 ortalaması en yüksek üç ay:")
print(ranked_months.head(3))
print("\nPM2.5 ortalaması en düşük üç ay:")
print(ranked_months.tail(3))

# Veri setinde tam takvim yılı bulunan 2014, 2015 ve 2016'yı karşılaştır.
plt.figure()
for year in [2014, 2015, 2016]:
    year_data = monthly_summary[monthly_summary["year"] == year]
    plt.plot(year_data["month"], year_data["mean"], label=str(year))

plt.xlabel("Ay")
plt.ylabel("Ortalama PM2.5 (µg/m³)")
plt.title("Aotizhongxin — Yıllara Göre Aylık PM2.5 Ortalamaları")
plt.xticks(range(1, 13))
plt.legend()
plt.savefig("outputs/09_year_comparison.png", dpi=150, bbox_inches="tight")
plt.show()

# Gözlem: Kış aylarında ortalamalar genel olarak yüksek olsa da aynı ayın
# ortalaması yıldan yıla değişebiliyor. Şubat 2014 ve Şubat 2016 buna örnek.
# Sıralamaları yorumlarken aylık eksik ölçüm yüzdelerini de dikkate al.


# 6. PM2.5 ve PM10 karşılaştırması
particle_data = df[["year", "month", "PM2.5", "PM10"]]
# İki kirleticinin de ölçüldüğü ortak kayıtları kullan.
particle_data = particle_data.dropna()

print("\nOrtak kayıtlarda PM2.5 ve PM10 özet istatistikleri:")
print(particle_data[["PM2.5", "PM10"]].describe())

plt.figure()
plt.scatter(particle_data["PM2.5"], particle_data["PM10"])
plt.xlabel("PM2.5 (µg/m³)")
plt.ylabel("PM10 (µg/m³)")
plt.title("PM2.5 - PM10 İlişkisi")
plt.savefig("outputs/10_pm25_pm10_scatter.png", dpi=150, bbox_inches="tight")
plt.show()

pm_corr = particle_data[["PM2.5", "PM10"]].corr()
print("\nPM2.5 ve PM10 korelasyonu:")
print(pm_corr)

particle_monthly = particle_data.groupby(["year", "month"], as_index=False).agg(
    pm25_mean=("PM2.5", "mean"),
    pm10_mean=("PM10", "mean")
)
particle_monthly = particle_monthly.sort_values(["year", "month"])

particle_month_text = particle_monthly["month"].astype(str)
particle_year_text = particle_monthly["year"].astype(str)
particle_monthly["period"] = particle_year_text + "-" + particle_month_text

# Bu ortalamalar ortak PM2.5-PM10 kayıtlarına dayanır. monthly_summary ise
# mevcut tüm PM2.5 ölçümlerini kullanır; sonuçların biraz farklı olması mümkündür.
plt.figure()
plt.plot(
    particle_monthly["period"],
    particle_monthly["pm25_mean"],
    label="PM2.5"
)
plt.plot(
    particle_monthly["period"],
    particle_monthly["pm10_mean"],
    label="PM10"
)
plt.xlabel("Yıl-Ay")
plt.ylabel("Ortalama konsantrasyon (µg/m³)")
plt.title("Aotizhongxin — Aylık PM2.5 ve PM10 Ortalamaları")
plt.legend()
plt.xticks(
    range(0, len(particle_monthly), 6),
    particle_monthly["period"].iloc[::6],
    rotation=45
)
plt.savefig("outputs/11_monthly_pm25_pm10.png", dpi=150, bbox_inches="tight")
plt.show()
