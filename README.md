

Tài liệu giúp người mới tiếp cận Python qua các phần: `if/else`, `for`, `while`, xử lý file Excel bằng `pandas`, và bài tập thực tế. Mỗi mục gồm **giải thích**, **code mẫu**, **input ví dụ**, **output ví dụ**.

---

## 1. ⚡ Cấu trúc điều kiện: `if`, `elif`, `else`

### 🔹 Code

```python
# Kiểm tra số âm, dương, hay bằng 0
n = int(n)  # n sẽ được nhập trong ví dụ bên dưới

if n > 0:
    print("Số dương")
elif n < 0:
    print("Số âm")
else:
    print("Bằng 0")
```

### 🔹 Input mô phỏng

```
n = 5
```

### 🔹 Output

```
Số dương
```

---

## 2. 🔁 Vòng lặp `for`

### Code

```python
# In ra các số từ 1 đến n
n = int(n)

for i in range(1, n+1):
    print(i)
```

### Input mô phỏng

```
n = 5
```

### Output

```
1
2
3
4
5
```

---

## 3. 🔄 Vòng lặp `while`

### Code

```python
# Đếm từ 1 đến n bằng while
n = int(n)
i = 1

while i <= n:
    print(i)
    i += 1  # tăng i lên 1
```

### Input mô phỏng

```
n = 3
```

### Output

```
1
2
3
```

---

## 4. 📁 Làm việc với Excel bằng pandas

### 4.1 Tạo file Excel

```python
import pandas as pd

# Tạo DataFrame
data = {
    "Ten": ["Phúc", "Lan", "Minh"],
    "Tuoi": [21, 22, 20]
}

df = pd.DataFrame(data)

# Xuất ra file Excel (không ghi cột index)
df.to_excel("demo.xlsx", index=False)
```

### File tạo ra: `demo.xlsx`

---

### 4.2 Đọc file Excel

```python
import pandas as pd
df = pd.read_excel("demo.xlsx")
print(df)
```

### Output mẫu

```
    Ten  Tuoi
0   Phúc    21
1    Lan    22
2   Minh    20
```

---

### 4.3 Thêm cột

```python
df["Diem"] = [9, 8, 7]
df.to_excel("demo.xlsx", index=False)
```

### 4.4 Xóa cột

```python
df = df.drop(columns=["Tuoi"])
df.to_excel("demo.xlsx", index=False)
```

### 4.5 Sửa giá trị trong cột

```python
df.loc[0, "Diem"] = 10  # sửa điểm dòng 0
```

---

### 4.6 Lọc dữ liệu

```python
# Lấy những người có điểm >= 8
df_loc = df[df["Diem"] >= 8]
```

### 4.7 Sắp xếp dữ liệu

```python
df_sorted = df.sort_values(by="Diem", ascending=False)
```

---

## 5. 📚 Bài tập tổng hợp

### Bài: Tính học phí dựa trên số tín chỉ

#### Code

```python
# x = đơn giá 1 tín chỉ
# n = số môn học
# list_tc = danh sách tín chỉ từng môn

x = int(x)
n = int(n)
list_tc = list_tc  # nhận từ ví dụ input bên dưới

tong_tc = sum(list_tc)
tong_tien = x * tong_tc

if tong_tien > 4_000_000:
    tong_tien = 4_000_000

print("Số tiền cần nộp:", tong_tien)
```

### Input mô phỏng

```
x = 470000
n = 3
list_tc = [3, 3, 2]
```

### Output

```
Số tiền cần nộp: 3760000
```

---

## 6. 💰 Bài tập: Tính lãi ngân hàng (lãi kép)

### Code

```python
a = float(a)        # số tiền gửi
lai = float(lai)    # lãi suất hàng tháng (% → chuyển về số thập phân)
m = int(m)          # số tháng

lai = lai / 100

# Nếu gửi hơn 12 tháng → tăng lãi suất thêm 0.02%
if m > 12:
    lai += 0.02 / 100

# Công thức lãi kép
tien_nhan = a * (1 + lai) ** m
print("Số tiền nhận được:", tien_nhan)
```

### Input mô phỏng

```
a = 1000000
lai = 0.5
m = 6
```

### Output

```
Số tiền nhận được: 1030150.0
```

---

# 🎉 Kết thúc

Nếu anh muốn:

* làm **file PDF**,
* chia thành **slide**,
* thêm bài tập trắc nghiệm,
* hoặc làm bản cực đơn cho học sinh cấp 2,

cứ nói em làm ngay nha! 🚀
