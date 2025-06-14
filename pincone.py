import pandas as pd
from pinecone import Pinecone

# === THÔNG TIN PINECONE CỦA BẠN ===
PINECONE_API_KEY = "pcsk_5RXjFo_6a75tCUJkS52pEcq5batuo9JQa6Gw9Hzy73GCNfqtYZXyzbwpvKofAHS6c83LpN"  
PINECONE_HOST = "https://fooddata-ggydovj.svc.aped-4627-b74a.pinecone.io"  
PINECONE_NAMESPACE = "default"        

# Khởi tạo Pinecone client mới
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=PINECONE_HOST)

# Đọc dữ liệu từ Excel
print("Đang đọc dữ liệu từ datamonan.xlsx ...")
df = pd.read_excel("datamonan.xlsx")
df.columns = df.columns.str.strip()


records = []
for idx, row in df.iterrows():

    def safe_get(field):
        val = row.get(field, '')
        if pd.isna(val):
            return ''
        return str(val)
    mon_an = safe_get('Món ăn')
    vung_mien = safe_get('Vùng miền')
    mo_ta = safe_get('Mô tả')
    nguyen_lieu = safe_get('Nguyên liệu')
    cach_lam = safe_get('Cách làm/công thức')
    link_mon_an = safe_get('Link món ăn')
    hinh_anh = safe_get('Hình ảnh')
    chay_man = safe_get('Chay/mặn')
    tam_trang_cam_xuc = safe_get('Tâm trạng, cảm xúc')
    chinh_vat = safe_get('Chính/vặt')
    kho_nuoc = safe_get('Khô/nước')
    # Ghép text cho embedding
    text_field = f"Món ăn: {mon_an}. Vùng miền: {vung_mien}. Mô tả: {mo_ta}. Nguyên liệu: {nguyen_lieu}. Cách làm: {cach_lam}. Link món ăn: {link_mon_an}. Hình ảnh: {hinh_anh}. Chay/mặn: {chay_man}. Tâm trạng, cảm xúc: {tam_trang_cam_xuc}. Chính/vặt: {chinh_vat}. Khô/nước: {kho_nuoc}."
 
    record = {
        "_id": str(idx),
        "text": text_field,
        "mon_an": mon_an,
        "vung_mien": vung_mien,
        "mo_ta": mo_ta,
        "nguyen_lieu": nguyen_lieu,
        "cach_lam": cach_lam,
        "link_mon_an": link_mon_an,
        "hinh_anh": hinh_anh,
        "chay_man": chay_man,
        "tam_trang_cam_xuc": tam_trang_cam_xuc,
        "chinh_vat": chinh_vat,
        "kho_nuoc": kho_nuoc
    }
    records.append(record)

# Upsert lên Pinecone (batch 96, do giới hạn của index)
print(f"Đang upsert {len(records)} records lên Pinecone ...")
for i in range(0, len(records), 96):
    batch = records[i:i+96]
    index.upsert_records(PINECONE_NAMESPACE, batch)
print("Đã upsert xong dữ liệu lên Pinecone!")

if __name__ == "__main__":
    # Xuất danh sách tên món đã upsert lên Pinecone
    from pinecone import Pinecone
    PINECONE_API_KEY = "pcsk_5RXjFo_6a75tCUJkS52pEcq5batuo9JQa6Gw9Hzy73GCNfqtYZXyzbwpvKofAHS6c83LpN"
    PINECONE_HOST = "https://fooddata-ggydovj.svc.aped-4627-b74a.pinecone.io"
    PINECONE_NAMESPACE = "default"
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(host=PINECONE_HOST)
    # Lấy 1000 vector đầu tiên (hoặc nhiều hơn nếu cần)
    results = index.query(namespace=PINECONE_NAMESPACE, top_k=1000, include_metadata=True, vector=[0.0]*384)
    print("Danh sách tên món trong Pinecone:")
    for match in results.get('matches', []):
        print(match['metadata'].get('mon_an', ''))
