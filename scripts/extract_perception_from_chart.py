import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ===== 1) image =====
img_path = "world_getting_worse_chart.png"   # put photo image

# ===== 2) order of the country (up -> down)=====
countries = [
    "Turkey", "Belgium", "Mexico", "South Korea", "Italy", "France",
    "South Africa", "Brazil", "Spain", "Argentina", "Canada", "Hong Kong",
    "Thailand", "Malaysia", "Poland", "Finland", "Australia", "United Kingdom",
    "Peru", "United States", "Germany", "Singapore", "Sweden", "Norway",
    "South Africa?", "United Arab Emirates", "Hungary", "Japan", "Denmark", "Russia"
]



# ===== 3) Scan image =====
img = cv2.imread(img_path)
if img is None:
    raise FileNotFoundError(f"Image not found: {img_path}")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# ===== 4) binary =====
# Extract gray bar
_, th = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY_INV)

# ===== 5) connect the bar =====
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 3))
th2 = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)

# ===== 6) extract the edge =====
contours, _ = cv2.findContours(th2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

bars = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)

    # keep only wide bar
    # set the threshold
    if w > 250 and 8 <= h <= 30:
        bars.append((x, y, w, h))

# y order
bars = sorted(bars, key=lambda t: t[1])

# ===== 7) check number of bars =====
print(f"Detected bars: {len(bars)}")

# visualize
debug = img.copy()
for i, (x, y, w, h) in enumerate(bars):
    cv2.rectangle(debug, (x, y), (x+w, y+h), (0, 0, 255), 2)
    cv2.putText(debug, str(i+1), (x+w+5, y+h), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

plt.figure(figsize=(10, 14))
plt.imshow(cv2.cvtColor(debug, cv2.COLOR_BGR2RGB))
plt.axis("off")
plt.show()

# ===== 8) set the position of 0% and 100% of the bar =====
# left: 0% , right: 100%
# adjust
x0 = 125   # start point of the bar（0%）
x100 = 990 # point of 100% 

# ===== 9) transfer: length → ratio  =====
results = []
n = min(len(countries), len(bars))

for i in range(n):
    x, y, w, h = bars[i]

    # actual right edge of the bar
    x_right = x + w

    # 0-100 scaling
    pct = (x_right - x0) / (x100 - x0) * 100
    pct = max(0, min(100, pct))

    results.append({
        "country": countries[i],
        "pct_answered_world_getting_worse": round(pct, 1)
    })

df = pd.DataFrame(results)

# ===== 10) extract =====
print(df)
df.to_csv("world_getting_worse_extracted.csv", index=False, encoding="utf-8-sig")
print("Saved: world_getting_worse_extracted.csv")