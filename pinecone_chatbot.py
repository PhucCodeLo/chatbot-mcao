import re
import unicodedata
from pinecone import Pinecone
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from intent.intent_cay import handle_intent_cay
from intent.intent_che import handle_intent_che
from intent.intent_banh import handle_intent_banh
from intent.intent_cach_lam import handle_intent_cach_lam
from intent.intent_nguyen_lieu import handle_intent_nguyen_lieu
from intent.intent_com import handle_intent_com
from intent.intent_mon_chay import handle_intent_mon_chay
from intent.intent_mon_man import handle_intent_mon_man
from intent.intent_mon_bun import handle_intent_mon_bun
from intent.intent_an_vat import handle_intent_an_vat
from intent.intent_an_chinh import handle_intent_an_chinh
from intent.intent_mon_kho import handle_intent_mon_kho
from intent.intent_mon_nuoc import handle_intent_mon_nuoc
from intent.intent_chao import handle_intent_chao
from intent.intent_vung_mien import handle_intent_vung_mien
from intent.intent_contact import handle_intent_contact
from intent.intent_hinh_anh import handle_intent_hinh_anh
from intent.intent_chi_tiet_mon import handle_intent_chi_tiet_mon
import random

# === Cấu hình Pinecone ===
PINECONE_API_KEY = "pcsk_5RXjFo_6a75tCUJkS52pEcq5batuo9JQa6Gw9Hzy73GCNfqtYZXyzbwpvKofAHS6c83LpN"
PINECONE_HOST = "https://fooddata-ggydovj.svc.aped-4627-b74a.pinecone.io"
PINECONE_NAMESPACE = "default"

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=PINECONE_HOST)

genai.configure(api_key="AIzaSyBOzGJFO9M3YdIet2mXfCPg4WDSU2ICrHE")
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def search_pinecone(query, top_k=500, filter_override=None):
    try:
        filters = filter_override if filter_override is not None else {}
        q_lower = query.lower()
        # Lọc vùng miền (dùng $eq) nếu chưa có filter_override
        if not filter_override:
            if "miền bắc" in q_lower or "bắc" in q_lower:
                filters["vung_mien"] = {"$eq": "Miền Bắc"}
            elif "miền nam" in q_lower or "nam" in q_lower:
                filters["vung_mien"] = {"$eq": "Miền Nam"}
            elif "miền trung" in q_lower or "trung" in q_lower:
                filters["vung_mien"] = {"$eq": "Miền Trung"}
        vector = embedder.encode([query])[0].tolist()
        if filters:
            results = index.query(
                namespace=PINECONE_NAMESPACE,
                top_k=top_k,
                include_metadata=True,
                vector=vector,
                filter=filters
            )
        else:
            results = index.query(
                namespace=PINECONE_NAMESPACE,
                top_k=top_k,
                include_metadata=True,
                vector=vector
            )
        matches = results['matches'] if 'matches' in results else []
        # Lọc lại theo từ khóa nếu có
        keyword = None
        if "bún" in q_lower:
            keyword = "bún"
        elif "phở" in q_lower:
            keyword = "phở"
        if keyword:
            matches = [m for m in matches if keyword in (m['metadata'].get('mon_an','').lower() + m['metadata'].get('mo_ta','').lower())]
        # Trả về đúng số lượng kết quả theo top_k
        return [match.get('metadata', {}) for match in matches[:top_k]]
    except Exception as e:
        import sys
        import traceback
        print("Lỗi truy vấn Pinecone:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return []


def get_bot_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def suggest_follow_up_questions():
    suggestions = [
        "Bạn muốn tham khảo thêm món ăn nào không?",
        "Bạn có muốn biết cách làm hoặc nguyên liệu của món nào không?",
        "Bạn cần gợi ý món đặc sắc, món chay, món vùng miền hay món ăn vặt không?",
        "Bạn muốn xem hình ảnh món ăn nào không?",
        "Bạn muốn biết giờ mở cửa, địa chỉ hoặc liên hệ nhà hàng không?",
        "Bạn muốn biết thêm về món nào vừa hỏi không?",
        "Bạn có muốn hỏi về món ăn phù hợp cho thời tiết hôm nay không?",
        "Bạn muốn biết món nào được yêu thích nhất tại nhà hàng không?"
    ]
    return random.choice(suggestions)

def normalize_text(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    return text.lower().strip()

def find_best_match(ten_mon_query, top_k_small=100, top_k_large=500):
    """Tìm món ăn khớp nhất với tên truy vấn, ưu tiên khớp hoàn toàn, sau đó partial match, sau đó fuzzy."""
    ten_mon_query_norm = normalize_text(ten_mon_query)
    query_words = set(ten_mon_query_norm.split())
    candidates = search_pinecone(ten_mon_query, top_k=top_k_small)
    # Ưu tiên khớp hoàn toàn
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        if ten_mon_query_norm == ten_mon_norm:
            return doc, candidates
    # Khớp từng từ (tất cả từ trong tên món phải có trong query, không cần đúng thứ tự)
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        ten_mon_words = set(ten_mon_norm.split())
        if ten_mon_words and ten_mon_words.issubset(query_words):
            return doc, candidates
    # Khớp in (tên món nằm trong query hoặc ngược lại, chỉ áp dụng nếu tên món > 2 ký tự)
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        if len(ten_mon_norm) > 2 and (ten_mon_norm in ten_mon_query_norm or ten_mon_query_norm in ten_mon_norm):
            return doc, candidates
    # Fuzzy: ít nhất 70% từ trong tên món có trong query
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        ten_mon_words = ten_mon_norm.split()
        if ten_mon_words:
            match_count = sum(1 for word in ten_mon_words if word in ten_mon_query_norm)
            if match_count / len(ten_mon_words) >= 0.7:
                return doc, candidates
    # Nếu vẫn không tìm thấy, thử lấy top_k lớn và lặp lại
    candidates = search_pinecone(ten_mon_query, top_k=top_k_large)
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        if ten_mon_query_norm == ten_mon_norm:
            return doc, candidates
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        ten_mon_words = set(ten_mon_norm.split())
        if ten_mon_words and ten_mon_words.issubset(query_words):
            return doc, candidates
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        if len(ten_mon_norm) > 2 and (ten_mon_norm in ten_mon_query_norm or ten_mon_query_norm in ten_mon_norm):
            return doc, candidates
    for doc in candidates:
        ten_mon = doc.get('mon_an', '')
        ten_mon_norm = normalize_text(ten_mon)
        ten_mon_words = ten_mon_norm.split()
        if ten_mon_words:
            match_count = sum(1 for word in ten_mon_words if word in ten_mon_query_norm)
            if match_count / len(ten_mon_words) >= 0.7:
                return doc, candidates
    return None, candidates

def is_greeting(text):
    """Nhận diện intent chào hỏi với nhiều biến thể phổ biến."""
    text = normalize_text(text)
    # Loại bỏ dấu câu cuối câu
    text = re.sub(r'[!,.?…]+$', '', text)
    # Regex nhận diện các biến thể chào hỏi
    return bool(re.match(r"^(xin chao|chao|hello|hi|hey)(\s+(ban|bạn|bạn oi|cả nhà|mọi người|cậu|cacs ban|các bạn|cả nhà|anh|chị|em|cả lớp|team|mọi nguoi|mọi người))?(\s|$)", text))

def check_mon_an_ton_tai(user_input, find_best_match):
    # Bao quát nhiều biến thể hỏi về sự tồn tại món ăn
    patterns = [
        # Dạng: nhà hàng/bạn/ở đây/quán/mình/bên mình có (bán/phục vụ) (món) ... không
        r"(?:nhà hàng|bạn|ở đây|quán|mình|bên mình)?\s*(có|có bán|có phục vụ)?\s*(món)?\s*([\w\sàáảãạâấầẩẫậăắằẳẵặèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\-]+?)\s*(không|ko|hông|hông vậy|không nhỉ|không ạ|không em|không anh|không chị|không bạn|không thế|không ta|không vậy|không hả|không à|không ha|không hở|không hén|không hen)?[\?\.,!]*$",
        # Dạng: có ... không
        r"có\s+([\w\sàáảãạâấầẩẫậăắằẳẵặèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\-]+?)\s+không"
    ]
    for pat in patterns:
        m = re.search(pat, user_input.lower())
        if m:
            # Ưu tiên lấy group có nội dung dài nhất làm tên món
            groups = [g for g in m.groups() if g]
            ten_mon_query = max(groups, key=len) if groups else None
            if ten_mon_query:
                ten_mon_query = ten_mon_query.strip()
                # Loại bỏ các từ dư thừa đầu câu ("món", "bán", "phục vụ", ...)
                ten_mon_query = re.sub(r"^(món|bán|phục vụ|có|ở đây|nhà hàng|bạn|quán|mình|bên mình)\s+", "", ten_mon_query)
                ten_mon_query_norm = normalize_text(ten_mon_query)
                query_words = set(ten_mon_query_norm.split())
                found, candidates = find_best_match(ten_mon_query)
                if found:
                    ten_mon_norm = normalize_text(found.get('mon_an',''))
                    ten_mon_words = set(ten_mon_norm.split())
                    # Chỉ trả lời 'có' nếu match exact hoặc all từ trong tên món đều có trong query và ngược lại
                    if ten_mon_query_norm == ten_mon_norm or (ten_mon_words and ten_mon_words.issubset(query_words) and query_words.issubset(ten_mon_words)):
                        return f"Dạ, nhà hàng Phúc Đẹp Chai có món {found.get('mon_an','')} nhé! Bạn muốn biết thêm về món này không?", True
            # Nếu không match exact hoặc all từ khớp 2 chiều, KHÔNG trả lời luôn, để intent nhóm tiếp tục xử lý
            return None, False
    return None, False

def main():
    # print("=== Chatbot MC ảo nhà hàng (Pinecone + Gemini 2.5 Flash) ===")
    welcome_bot = (
        "Chào khách iu! Tớ là MC ảo của nhà hàng Phúc Đẹp Chai, sẵn sàng giúp bạn với các món ăn, thực đơn, "
        "và mọi thắc mắc về nhà hàng. Bạn cần hỏi gì cứ thoải mái nhé!"
    )
    print(f"Bot: {welcome_bot}")
    history = [{"user": "", "bot": welcome_bot}]
    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ["exit", "thoát", "quit"]:
            print("Kết thúc phiên chat.")
            break
        # Xử lý chào hỏi, small talk (tối ưu nhận diện)
        if is_greeting(user_input):
            answer = "Chào khách iu bạn! Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Khách iu muốn tìm hiểu về món ăn, thực đơn, nguyên liệu hay cần gợi ý món gì không? Hãy đặt câu hỏi cho tớ nhé!"
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue

        # Intent: Nhận diện truy vấn cách làm <tên món> hoặc công thức <tên món>
        answer = handle_intent_cach_lam(user_input, history, find_best_match, get_bot_response)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue

            
        # Intent: Nhận diện truy vấn nguyên liệu làm <tên món> hoặc nguyên liệu <tên món>
        answer = handle_intent_nguyen_lieu(user_input, history, find_best_match, get_bot_response)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer})
            continue

        # Intent: Gợi ý các món cay nếu user hỏi về món cay
        answer, mon_cay_suggested = handle_intent_cay(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_cay_suggested": mon_cay_suggested})
            continue

        # Intent: Gợi ý các món chè nếu user hỏi về chè
        answer, mon_che_suggested = handle_intent_che(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_che_suggested": mon_che_suggested})
            continue

        # Intent: Gợi ý các món bánh nếu user hỏi về bánh
        answer, mon_banh_suggested = handle_intent_banh(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_banh_suggested": mon_banh_suggested})
            continue


        # Intent: Gợi ý các món cơm nếu user hỏi về cơm
        answer, mon_com_suggested = handle_intent_com(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_com_suggested": mon_com_suggested})
            continue

        # Intent: Gợi ý các món chay nếu user hỏi về món chay
        answer, mon_chay_suggested = handle_intent_mon_chay(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_chay_suggested": mon_chay_suggested})
            continue

        # Intent: Gợi ý các món mặn nếu user hỏi về món mặn
        answer, mon_man_suggested = handle_intent_mon_man(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_man_suggested": mon_man_suggested})
            continue

        # Intent: Gợi ý các món bún nếu user hỏi về bún
        answer, mon_bun_suggested = handle_intent_mon_bun(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_bun_suggested": mon_bun_suggested})
            continue

        # Intent: Gợi ý các món ăn vặt nếu user hỏi về ăn vặt
        answer, mon_vat_suggested = handle_intent_an_vat(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_vat_suggested": mon_vat_suggested})
            continue

        # Intent: Gợi ý các món chính nếu user hỏi về món chính
        answer, mon_chinh_suggested = handle_intent_an_chinh(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_chinh_suggested": mon_chinh_suggested})
            continue

        # Intent: Gợi ý các món khô nếu user hỏi về món khô
        answer, mon_kho_suggested = handle_intent_mon_kho(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_kho_suggested": mon_kho_suggested})
            continue


        # Intent: Gợi ý các món nước nếu user hỏi về món nước
        answer, mon_nuoc_suggested = handle_intent_mon_nuoc(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_nuoc_suggested": mon_nuoc_suggested})
            continue

        # Intent: Gợi ý các món cháo nếu user hỏi về cháo
        answer, mon_chao_suggested = handle_intent_chao(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_chao_suggested": mon_chao_suggested})
            continue

        # Intent: Gợi ý các món ăn theo vùng miền nếu user hỏi về miền Bắc, Trung, Nam
        answer, mon_vung_mien_suggested = handle_intent_vung_mien(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
        if answer:
            print("Bot:", answer)
            history.append({"user": user_input, "bot": answer, "mon_vung_mien_suggested": mon_vung_mien_suggested})
            continue
        else:
            pass  
 
def chat_with_bot(user_input, history=None):
    """Hàm này nhận user_input và history, trả về bot_response và history mới."""
    if history is None:
        welcome_bot = (
            "Chào khách iu! Tớ là MC ảo của nhà hàng Phúc Đẹp Chai, sẵn sàng giúp bạn với các món ăn, thực đơn, "
            "và mọi thắc mắc về nhà hàng. Bạn cần hỏi gì cứ thoải mái nhé!"
        )
        history = [{"user": "", "bot": welcome_bot}]
    if user_input.lower() in ["exit", "thoát", "quit"]:
        return "Kết thúc phiên chat.", history
    if is_greeting(user_input):
        answer = "Chào khách iu bạn! Mình là MC ảo của nhà hàng Phúc Đẹp Chai. Khách iu muốn tìm hiểu về món ăn, thực đơn, nguyên liệu hay cần gợi ý món gì không? Hãy đặt câu hỏi cho tớ nhé!"
        history.append({"user": user_input, "bot": answer})
        return answer, history
    # Intent hình ảnh món ăn (ưu tiên trên intent món)
    answer = handle_intent_hinh_anh(user_input, find_best_match)
    if answer:
        history.append({"user": user_input, "bot": answer})
        return answer, history
    # Intent chi tiết món (nếu user xác nhận muốn biết thêm)
    answer = handle_intent_chi_tiet_mon(user_input, history, find_best_match)
    if answer:
        history.append({"user": user_input, "bot": answer})
        return answer, history
    # ƯU TIÊN kiểm tra intent hỏi contact (địa chỉ, sđt, website,...) trước các intent khác
    answer = handle_intent_contact(user_input)
    if answer:
        history.append({"user": user_input, "bot": answer})
        return answer, history
    # ƯU TIÊN kiểm tra intent hỏi sự tồn tại món ăn trước các intent nhóm
    answer, found_exact = check_mon_an_ton_tai(user_input, find_best_match)
    if answer:
        history.append({"user": user_input, "bot": answer})
        if found_exact:
            return answer, history
        # Nếu không tìm thấy exact, vẫn tiếp tục xử lý intent nhóm bên dưới
    answer = handle_intent_cach_lam(user_input, history, find_best_match, get_bot_response)
    if answer:
        history.append({"user": user_input, "bot": answer})
        return answer, history
    answer = handle_intent_nguyen_lieu(user_input, history, find_best_match, get_bot_response)
    if answer:
        history.append({"user": user_input, "bot": answer})
        return answer, history
    answer, mon_cay_suggested = handle_intent_cay(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_cay_suggested": mon_cay_suggested})
        return answer, history
    answer, mon_che_suggested = handle_intent_che(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_che_suggested": mon_che_suggested})
        return answer, history
    answer, mon_banh_suggested = handle_intent_banh(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_banh_suggested": mon_banh_suggested})
        return answer, history
    answer, mon_com_suggested = handle_intent_com(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_com_suggested": mon_com_suggested})
        return answer, history
    answer, mon_chay_suggested = handle_intent_mon_chay(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_chay_suggested": mon_chay_suggested})
        return answer, history
    answer, mon_man_suggested = handle_intent_mon_man(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_man_suggested": mon_man_suggested})
        return answer, history
    answer, mon_bun_suggested = handle_intent_mon_bun(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_bun_suggested": mon_bun_suggested})
        return answer, history
    answer, mon_vat_suggested = handle_intent_an_vat(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_vat_suggested": mon_vat_suggested})
        return answer, history
    answer, mon_chinh_suggested = handle_intent_an_chinh(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_chinh_suggested": mon_chinh_suggested})
        return answer, history
    answer, mon_kho_suggested = handle_intent_mon_kho(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_kho_suggested": mon_kho_suggested})
        return answer, history
    answer, mon_nuoc_suggested = handle_intent_mon_nuoc(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_nuoc_suggested": mon_nuoc_suggested})
        return answer, history
    answer, mon_chao_suggested = handle_intent_chao(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_chao_suggested": mon_chao_suggested})
        return answer, history
    answer, mon_vung_mien_suggested = handle_intent_vung_mien(user_input, history, search_pinecone, normalize_text, suggest_follow_up_questions)
    if answer:
        history.append({"user": user_input, "bot": answer, "mon_vung_mien_suggested": mon_vung_mien_suggested})
        return answer, history
    # Nếu không nhận diện được intent
    # dùng LLM đóng vai MC ảo để trả lời linh hoạt
    # Nếu không nhận diện được intent, dùng LLM nhưng kiểm soát hallucination bằng cách cung cấp dữ liệu thật
    # Truy vấn Pinecone lấy top 15 món ăn thực tế
    real_dishes = search_pinecone("", top_k=10)
    if real_dishes:
        dish_list = "\n".join(f"- {d.get('mon_an','')} (Vùng miền: {d.get('vung_mien','')}): {d.get('mo_ta','')}" for d in real_dishes if d.get('mon_an'))
        prompt = (
            "Bạn là MC ảo của nhà hàng Phúc Đẹp Chai. Dưới đây là danh sách các món ăn hiện có trong nhà hàng:\n"
            f"{dish_list}\n"
            "Chỉ được gợi ý, trả lời dựa trên danh sách trên, không được bịa thêm món ngoài danh sách.\n"
            "Nếu khách hỏi về thời tiết, thời điểm, hãy gợi ý món phù hợp trong danh sách. Nếu không rõ, hãy hỏi lại khách để hiểu rõ hơn nhu cầu.\n"
            f"Lịch sử hội thoại gần nhất: {history[-3:] if history else ''}\n"
            f"Khách hỏi: {user_input}\n"
            "MC trả lời:"
        )
    else:
        prompt = (
            "Bạn là MC ảo của nhà hàng Phúc Đẹp Chai. Hãy trả lời thân thiện, tự nhiên, gợi ý món ăn phù hợp với ngữ cảnh (thời gian, thời tiết, cảm xúc, v.v) hoặc giải đáp các thắc mắc về nhà hàng. "
            "Nếu khách hỏi về thời tiết, thời điểm, hãy gợi ý món phù hợp. Nếu không rõ, hãy hỏi lại khách để hiểu rõ hơn nhu cầu.\n"
            f"Lịch sử hội thoại gần nhất: {history[-3:] if history else ''}\n"
            f"Khách hỏi: {user_input}\n"
            "MC trả lời:"
        )
    answer = get_bot_response(prompt)
    history.append({"user": user_input, "bot": answer})
    return answer, history

if __name__ == "__main__":
    main()
