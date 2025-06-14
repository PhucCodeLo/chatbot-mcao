import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import re
import unicodedata

# Cấu hình API Google Gemini
genai.configure(api_key="AIzaSyBOzGJFO9M3YdIet2mXfCPg4WDSU2ICrHE")

# Load model embedding local
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Đường dẫn file cache
EMBEDDING_PATH = "embeddings.npy"
FAISS_INDEX_PATH = "faiss.index"

# Load dữ liệu món ăn từ Excel
if os.path.exists(EMBEDDING_PATH) and os.path.exists(FAISS_INDEX_PATH):
    print("Đang load embedding và FAISS index từ cache ...")
    embeddings = np.load(EMBEDDING_PATH)
    dimension = embeddings.shape[1]
    index = faiss.read_index(FAISS_INDEX_PATH)
    # Đảm bảo documents vẫn được tạo để truy xuất
    df = pd.read_excel("datamonan.xlsx")
    df.columns = df.columns.str.strip()
    documents = []
    for idx, row in df.iterrows():
        mon_an = row.get('Món ăn', '')
        vung_mien = row.get('Vùng miền', '')
        mo_ta = row.get('Mô tả', '')
        nguyen_lieu = row.get('Nguyên liệu', '')
        cach_lam = row.get('Cách làm/công thức', '')
        link_mon_an = row.get('Link món ăn', '')
        hinh_anh = row.get('Hình ảnh', '')
        chay_man = row.get('Chay/mặn', '')
        tam_trang_cam_xuc = row.get('Tâm trạng, cảm xúc', '')
        chinh_vat = row.get('Chính/vặt', '')
        kho_nuoc = row.get('Khô/nước', '')
        text = (
            f"Món ăn: {mon_an}. "
            f"Vùng miền: {vung_mien}. "
            f"Mô tả: {mo_ta}. "
            f"Nguyên liệu: {nguyen_lieu}. "
            f"Cách làm: {cach_lam}. "
            f"Link món ăn: {link_mon_an}. "
            f"Hình ảnh: {hinh_anh}. "
            f"Chay/mặn: {chay_man}. "
            f"Tâm trạng, cảm xúc: {tam_trang_cam_xuc}. "
            f"Chính/vặt: {chinh_vat}. "
            f"Khô/nước: {kho_nuoc}."
        )
        documents.append(text)
else:
    # Load dữ liệu món ăn từ Excel
    df = pd.read_excel("datamonan.xlsx")
    df.columns = df.columns.str.strip()  # bỏ khoảng trắng thừa tên cột

    # Tạo documents chứa thông tin món ăn đầy đủ các trường
    documents = []
    for idx, row in df.iterrows():
        mon_an = row.get('Món ăn', '')
        vung_mien = row.get('Vùng miền', '')
        mo_ta = row.get('Mô tả', '')
        nguyen_lieu = row.get('Nguyên liệu', '')
        cach_lam = row.get('Cách làm/công thức', '')
        link_mon_an = row.get('Link món ăn', '')
        hinh_anh = row.get('Hình ảnh', '')
        chay_man = row.get('Chay/mặn', '')
        tam_trang_cam_xuc = row.get('Tâm trạng, cảm xúc', '')
        chinh_vat = row.get('Chính/vặt', '')
        kho_nuoc = row.get('Khô/nước', '')

        text = (
            f"Món ăn: {mon_an}. "
            f"Vùng miền: {vung_mien}. "
            f"Mô tả: {mo_ta}. "
            f"Nguyên liệu: {nguyen_lieu}. "
            f"Cách làm: {cach_lam}. "
            f"Link món ăn: {link_mon_an}. "
            f"Hình ảnh: {hinh_anh}. "
            f"Chay/mặn: {chay_man}. "
            f"Tâm trạng, cảm xúc: {tam_trang_cam_xuc}. "
            f"Chính/vặt: {chinh_vat}. "
            f"Khô/nước: {kho_nuoc}."
        )
        documents.append(text)

    print("Tạo embedding cho documents ...")
    embeddings = embedder.encode(documents, convert_to_numpy=True, show_progress_bar=True).astype('float32')

    # Tạo FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    # Lưu embedding và index ra file
    np.save(EMBEDDING_PATH, embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print("Đã lưu embedding và FAISS index ra file.")

# Bộ câu mẫu cho từng intent preset
intent_templates = {
    "địa chỉ": [
        "Địa chỉ nhà hàng ở đâu?",
        "Bạn có thể cho tôi biết địa chỉ không?",
        "Nhà hàng tọa lạc ở đâu?",
    ],
    "giờ mở cửa": [
        "Nhà hàng mở cửa mấy giờ?",
        "Giờ làm việc của nhà hàng là khi nào?",
        "Bạn mở cửa lúc mấy giờ?",
    ],
    "số món ăn": [
        "Nhà hàng có bao nhiêu món ăn?",
        "Số lượng món ăn trong thực đơn là bao nhiêu?",
        "Có bao nhiêu món ăn trong nhà hàng?"
        "Nhà hàng của bạn có bao nhiêu món ăn?",
    ],
    "giới thiệu": [
        "Bạn là ai?",
        "Giới thiệu về nhà hàng đi",
        "Nhà hàng của bạn như thế nào?",
        "Xin chào",
    ],
    "cảm ơn": [
        "Cảm ơn bạn",
        "Thanks",
        "Cảm ơn nhiều",
    ],
    "món chay": [
        "Bạn có món chay không?",
        "Cho tôi xem vài món chay",
        "Món ăn chay của nhà hàng là gì?",
    ],
    "món nước": [
        "Bạn có món nước không?",
        "Món nước nào ngon?",
        "Gợi ý món nước",
    ],
}

# Tạo embedding cho câu mẫu
intent_embeddings = {}
for intent, templates in intent_templates.items():
    intent_embeddings[intent] = embedder.encode(templates, convert_to_numpy=True)

# Câu trả lời preset tương ứng
preset_answers = {
    "giới thiệu": "Chào bạn! Mình là MC ảo của nhà hàng XYZ, sẵn sàng hỗ trợ bạn tìm món ăn, hỏi thực đơn, giờ mở cửa,...",
    "địa chỉ": "Nhà hàng XYZ tọa lạc tại số 123 Đường ABC, Quận 1, TP.HCM.",
    "giờ mở cửa": "Nhà hàng mở cửa từ 9h sáng đến 10h tối mỗi ngày.",
    "số món ăn": f"Hiện tại nhà hàng đang có tổng cộng {len(documents)} món ăn đặc sắc.",
    "cảm ơn": "Rất vui được hỗ trợ bạn! Hẹn gặp lại tại nhà hàng XYZ nhé.",
}

def extract_field(doc, field):
    # Lấy giá trị trường theo tên field, lấy hết đến trường tiếp theo (dấu chấm, khoảng trắng, chữ hoa, rồi dấu hai chấm) hoặc hết chuỗi
    pattern = rf"{field}: (.*?)(?=\. [A-ZÀ-Ỹ][^:]{2,20}: |$)"
    match = re.search(pattern, doc, re.DOTALL)
    if match:
        value = match.group(1).strip()
        return value
    return ""

def find_best_intent(user_input, threshold=0.7):
    user_emb = embedder.encode([user_input], convert_to_numpy=True)[0]
    best_intent = None
    best_score = -1
    for intent, embeddings in intent_embeddings.items():
        sims = np.inner(embeddings, user_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(user_emb) + 1e-10)
        max_sim = sims.max()
        if max_sim > best_score and max_sim > threshold:
            best_score = max_sim
            best_intent = intent
    return best_intent

def retrieve_similar_doc(query, top_k=3):
    query_emb = embedder.encode([query], convert_to_numpy=True).astype('float32')
    distances, indices = index.search(query_emb, top_k)
    return [documents[i] for i in indices[0]]

def build_prompt(history, retrieved_docs, user_question):
    history_text = ""
    for turn in history[-5:]:
        history_text += f"User: {turn['user']}\nBot: {turn['bot']}\n"
    docs_text = "\n\n".join(retrieved_docs)
    prompt = (
        f"Dữ liệu tham khảo:\n{docs_text}\n\n"
        f"Lịch sử hội thoại:\n{history_text}\n"
        f"User hỏi: {user_question}\n"
        f"Bot trả lời:"
    )
    return prompt

def get_bot_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def suggest_follow_up_questions():
    return "\nBạn muốn tham khảo thêm món nào nữa không? Hoặc bạn cần biết giờ mở cửa, địa chỉ nhà hàng, hay các món đặc sắc khác?"

def main():
    print("=== Chatbot MC ảo nhà hàng (Embedding + FAISS + Gemini 2.5 Flash + Preset prompt nâng cao) ===")

    welcome_bot = (
        "Chào bạn! Mình là MC ảo của nhà hàng XYZ, sẵn sàng giúp bạn với các món ăn, thực đơn, "
        "và mọi thắc mắc về nhà hàng. Bạn cần hỏi gì cứ thoải mái nhé!"
    )
    print(f"Bot: {welcome_bot}")
    history = [{"user": "", "bot": welcome_bot}]

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ["exit", "thoát", "quit"]:
            print("Kết thúc phiên chat.")
            break

        # --- Ưu tiên xử lý truy vấn thuộc tính dựa trên món ăn gần nhất trong lịch sử ---
        attr_patterns = [
            (r"nguyên liệu", "Nguyên liệu"),
            (r"cách làm|công thức", "Cách làm/công thức"),
            (r"giá", "Giá"),
            (r"loại nhân", "Mô tả"),
            (r"ăn kèm", "Mô tả"),
        ]
        attr_field = None
        for pat, field in attr_patterns:
            if re.search(pat, user_input.lower()):
                attr_field = field
                break
        # Nếu là truy vấn thuộc tính và có món ăn gần nhất trong lịch sử
        if attr_field:
            # Tìm món ăn gần nhất trong history
            last_dish = None
            for turn in reversed(history):
                # Tìm tên món ăn trong câu trả lời gần nhất của bot hoặc user
                match = re.search(r"bánh căn|món ăn: ([^.,\n]+)", turn.get("bot", "") + " " + turn.get("user", ""), re.IGNORECASE)
                if match:
                    last_dish = match.group(0) if match.group(0) != "món ăn" else match.group(1)
                    break
            if last_dish:
                # Tìm document tương ứng
                doc = next((doc for doc in documents if last_dish.lower() in doc.lower()), None)
                if doc:
                    value = extract_field(doc, attr_field)
                    if value:
                        answer = f"{attr_field} của {last_dish}: {value}"
                    else:
                        answer = f"Xin lỗi, hiện chưa có thông tin {attr_field.lower()} cho món {last_dish}."
                    answer += suggest_follow_up_questions()
                    print("Bot:", answer)
                    history.append({"user": user_input, "bot": answer})
                    continue

        # --- Ưu tiên trả lời thuộc tính món ăn dựa trên lịch sử hội thoại ---
        # Các từ khóa thuộc tính
        field_keywords = {
            "nguyên liệu": "Nguyên liệu",
            "cách làm": "Cách làm",
            "công thức": "Cách làm",
            "giá": "Giá",
            "loại nhân": "Nhân",
            "ăn kèm": "Ăn kèm",
        }
        field_matched = None
        for k in field_keywords:
            if k in user_input.lower():
                field_matched = field_keywords[k]
                break
        # Nếu user hỏi về thuộc tính mà không nhắc tên món, lấy món gần nhất từ history
        if field_matched:
            # Tìm món ăn gần nhất user vừa hỏi trong history
            last_dish = None
            for turn in reversed(history):
                # Ưu tiên tìm trong các câu bot trả lời có "Món ăn: <tên>"
                match = re.search(r"Món ăn: ([^\.]+)", turn.get("bot", ""))
                if match:
                    last_dish = match.group(1).strip()
                    break
                # Hoặc lấy tên món user vừa hỏi
                if turn.get("user") and len(turn["user"]) < 30:
                    # Kiểm tra tên món có trong danh sách
                    for doc in documents:
                        ten_mon = doc.split("Món ăn: ")[1].split(".")[0].strip()
                        if turn["user"].lower() in ten_mon.lower():
                            last_dish = ten_mon
                            break
                if last_dish:
                    break
            if last_dish:
                # Tìm doc tương ứng
                doc = next((d for d in documents if last_dish.lower() in d.split("Món ăn: ")[1].split(".")[0].lower()), None)
                if doc:
                    value = extract_field(doc, field_matched)
                    if value:
                        answer = f"{field_matched} của món {last_dish}: {value}"
                        answer += suggest_follow_up_questions()
                        print("Bot:", answer)
                        history.append({"user": user_input, "bot": answer})
                        continue
            # Nếu không tìm được món, fallback như cũ

        # --- ƯU TIÊN INTENT PRESET CHO THÔNG TIN NHÀ HÀNG ---
        intent = find_best_intent(user_input)
        preset_intent_nhahang = ["giới thiệu", "địa chỉ", "giờ mở cửa", "cảm ơn", "số món ăn"]
        if intent in preset_intent_nhahang:
            answer = preset_answers[intent]
            answer += suggest_follow_up_questions()
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue
        # --- XỬ LÝ ĐẶC BIỆT CÁC INTENT MÓN ĂN (món chay, món nước, món chè, ...) ---
        if intent == "món chay":
            def normalize(text):
                text = text.lower()
                text = unicodedata.normalize('NFD', text)
                text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
                return text
            chay_docs = []
            for doc in documents:
                # Lọc đúng món chay: trường Chay/mặn là 'chay' hoặc tên món/mô tả có từ 'chay' nhưng loại trừ các món không phải món chay thật sự
                chay_man = extract_field(doc, "Chay/mặn")
                ten_mon = doc.split("Món ăn: ")[1].split(".")[0].strip()
                mo_ta = extract_field(doc, "Mô tả")
                is_chay = False
                if chay_man and normalize(chay_man) == "chay":
                    is_chay = True
                elif "chay" in normalize(ten_mon) or "chay" in normalize(mo_ta):
                    # Loại trừ các món có từ 'chay' nhưng thực chất là món mặn (ví dụ: 'không chay', 'mặn', ...)
                    if not ("khong chay" in normalize(ten_mon) or "khong chay" in normalize(mo_ta) or "man" in normalize(chay_man)):
                        is_chay = True
                if is_chay:
                    chay_docs.append(doc)
            if not chay_docs:
                answer = "Xin lỗi, hiện nhà hàng chưa có món chay nào trong dữ liệu. Nếu bạn có thực đơn chay hoặc nguyên liệu chay, hãy cung cấp để mình hỗ trợ tốt hơn."
            else:
                answer_lines = ["Dưới đây là một số món chay gợi ý bạn có thể thích:"]
                for doc in chay_docs[:5]:
                    ten_mon = doc.split("Món ăn: ")[1].split(".")[0].strip()
                    vung_mien = extract_field(doc, "Vùng miền")
                    mo_ta = extract_field(doc, "Mô tả")
                    line = f"- {ten_mon}"
                    if vung_mien:
                        line += f" ({vung_mien})"
                    if mo_ta:
                        line += f": {mo_ta}"
                    answer_lines.append(line)
                answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue
        if intent == "món nước":
            nuoc_docs = [doc for doc in documents if "Khô/nước: Nước" in doc]
            if not nuoc_docs:
                answer = "Xin lỗi, hiện nhà hàng chưa có món nước nào trong dữ liệu."
            else:
                answer_lines = ["Dưới đây là một số món nước gợi ý bạn có thể thích:"]
                for doc in nuoc_docs[:5]:
                    ten_mon = doc.split("Món ăn: ")[1].split(".")[0]
                    mo_ta = extract_field(doc, "Mô tả")
                    answer_lines.append(f"- {ten_mon}: {mo_ta}")
                answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue
        # --- Nếu không phải intent preset, ưu tiên RAG + LLM như hiện tại ---
        # 1. Truy xuất các documents liên quan nhất
        retrieved_docs = retrieve_similar_doc(user_input, top_k=3)
        # 2. Xây dựng prompt cho LLM với dữ liệu + lịch sử hội thoại
        prompt = build_prompt(history, retrieved_docs, user_input)
        # 3. Lấy câu trả lời từ LLM
        bot_reply = get_bot_response(prompt)
        # 4. Nếu LLM trả về rỗng hoặc không liên quan, fallback trả lời mặc định
        if not bot_reply or len(bot_reply.strip()) < 5:
            answer = "Xin lỗi, mình chưa có thông tin phù hợp cho câu hỏi này. Bạn có thể hỏi về món ăn, nguyên liệu, cách làm, vùng miền..."
        else:
            answer = bot_reply
        answer += suggest_follow_up_questions()
        print("Bot:", answer)
        history.append({"user": user_input, "bot": answer})
        continue

        # Xử lý riêng cho intent "món chay"
        if intent == "món chay":
            def normalize(text):
                text = text.lower()
                text = unicodedata.normalize('NFD', text)
                text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
                return text
            chay_docs = [doc for doc in documents if (
                "chay" in normalize(doc.split("Chay/mặn:")[1].split(".")[0])
                if "Chay/mặn:" in doc else False
            ) or ("chay" in normalize(doc.split("Món ăn: ")[1].split(".")[0]))
              or ("chay" in normalize(extract_field(doc, "Mô tả")))]
            if not chay_docs:
                answer = "Xin lỗi, hiện nhà hàng chưa có món chay nào trong dữ liệu. Nếu bạn có thực đơn chay hoặc nguyên liệu chay, hãy cung cấp để mình hỗ trợ tốt hơn."
            else:
                answer_lines = ["Dưới đây là một số món chay gợi ý bạn có thể thích:"]
                for doc in chay_docs[:3]:
                    ten_mon = doc.split("Món ăn: ")[1].split(".")[0]
                    mo_ta = extract_field(doc, "Mô tả")
                    answer_lines.append(f"- {ten_mon}: {mo_ta}")
                answer = "\n".join(answer_lines)
            answer += suggest_follow_up_questions()
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue

        # --- Ưu tiên nhận diện truy vấn dạng "cách làm <tên món>" hoặc "công thức <tên món>" ---
        match_cachlam = re.match(r"(cách làm|công thức) (.+)", user_input.lower())
        if match_cachlam:
            ten_mon_query = match_cachlam.group(2).strip()
            # Tìm document khớp nhất với tên món
            def normalize(text):
                text = text.lower()
                text = unicodedata.normalize('NFD', text)
                text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
                return text
            ten_mon_query_norm = normalize(ten_mon_query)
            found_doc = None
            for doc in documents:
                ten_mon = doc.split("Món ăn: ")[1].split(".")[0].strip()
                if ten_mon_query_norm in normalize(ten_mon):
                    found_doc = doc
                    break
            if found_doc:
                cach_lam = extract_field(found_doc, "Cách làm")
                if not cach_lam:
                    cach_lam = extract_field(found_doc, "Cách làm/công thức")
                if cach_lam:
                    answer = f"Cách làm món {ten_mon_query}: {cach_lam}"
                else:
                    answer = f"Xin lỗi, hiện chưa có thông tin cách làm cho món {ten_mon_query}."
                answer += suggest_follow_up_questions()
                print("Bot:", answer)
                history.append({"user": user_input, "bot": answer})
                continue

if __name__ == "__main__":
    main()

