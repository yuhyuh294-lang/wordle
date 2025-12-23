from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import json
import uuid
import os

# Import các module vệ tinh
from database import init_db, save_game
from wordle_engine import evaluate
from ai_solver import WordleAISolver
# Import bộ sinh toán học
from math_gen import generate_equation

# Cho phép Flask tìm file html, css, js ở thư mục hiện tại (.)
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Route mặc định: Khi vào trang chủ sẽ hiện file index.html
@app.route('/')
def index():
    return app.send_static_file('index.html')

init_db()
MAX_TURNS = 6

# ==============================
# 1. LOAD DỮ LIỆU TIẾNG VIỆT (AN TOÀN)
# ==============================
def load_vietnamese_words():
    # Thử các đường dẫn có thể xảy ra
    candidates = ["words_vi.json", "data/words_vi.json"]
    filename = None
    
    for path in candidates:
        if os.path.exists(path):
            filename = path
            break
            
    if not filename:
        print("⚠️ CẢNH BÁO: Không tìm thấy file words_vi.json. Dùng danh sách mẫu.")
        return ["thanh", "hạnhphúc", "bạnbè"], {}

    try:
        with open(filename, encoding="utf-8") as f:
            raw = json.load(f)
            # Clean data: Xóa khoảng trắng, giữ nguyên dấu
            cleaned = list(set([w.strip().replace(" ", "").lower() for w in raw if len(w) >= 3]))
            
            # Map theo độ dài: {5: ['thanh', ...], 6: ['banbe', ...]}
            words_map = {}
            for w in cleaned:
                l = len(w)
                if l not in words_map: words_map[l] = []
                words_map[l].append(w)
            
            print(f"✅ Đã load Tiếng Việt: {len(cleaned)} từ.")
            return cleaned, words_map
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return ["thanh", "hạnhphúc"], {}

# Load dữ liệu ngay khi chạy server
ALL_WORDS_VI, MAP_WORDS_VI = load_vietnamese_words()

ACTIVE_GAMES = {}

# ==============================
# 2. LOGIC GỢI Ý
# ==============================
def ai_generate_hint(game):
    answer = game["answer"]
    mode = game["mode"]
    level = game["hint_level"]
    hint_msg = ""
    
    if mode == "math":
        lhs, rhs = answer.split('=')
        if level == 0: hint_msg = f"🔍 Cấp 1: Kết quả là {rhs}."
        elif level == 1: 
            ops = [c for c in "+-*/" if c in lhs]
            hint_msg = f"🔍 Cấp 2: Phép tính dùng dấu '{', '.join(set(ops))}'."
        else:
            idx = random.randint(0, len(answer)-1)
            hint_msg = f"🔍 Cấp 3: Vị trí {idx+1} là '{answer[idx]}'."
    else:
        if level == 0:
            hint_msg = f"🔍 Cấp 1: Từ có {len(answer)} ký tự."
        elif level == 1:
            char_in = random.choice(list(set(answer)))
            hint_msg = f"🔍 Cấp 2: Có chứa chữ '{char_in.upper()}'."
        else:
            idx = random.randint(0, len(answer)-1)
            hint_msg = f"🔍 Cấp 3: Vị trí {idx+1} là '{answer[idx].upper()}'."

    if level < 2: game["hint_level"] += 1
    return hint_msg

# ==============================
# ROUTES
# ==============================

@app.route("/start", methods=["POST"])
def start_game():
    data = request.json
    username = data.get("username", "guest")
    mode = data.get("mode", "vi")
    strict = data.get("strict", False)

    answer = ""
    ai_candidates = []

    # --- CHẾ ĐỘ TOÁN HỌC ---
    if mode == "math":
        # 1. Sinh đáp án Toán học ngẫu nhiên (độ dài 5 đến 8)
        target_len = random.randint(5, 8) 
        answer = generate_equation(target_len)
        
        # 2. QUAN TRỌNG: Sinh pool giả cho AI 
        # (Tạo 100 phép tính khác cùng độ dài để AI có cái mà chọn, không thì nó bị lỗi)
        ai_candidates = set()
        ai_candidates.add(answer) # Phải có đáp án trong pool
        
        # Cố gắng sinh thêm 100 phép tính giả
        attempts = 0
        while len(ai_candidates) < 100 and attempts < 500:
            attempts += 1
            eq = generate_equation(target_len)
            ai_candidates.add(eq)
            
        ai_candidates = list(ai_candidates)
        
    # --- CHẾ ĐỘ TIẾNG VIỆT ---
    else:
        pool_map = MAP_WORDS_VI
        # Chỉ chọn những độ dài mà có ít nhất 5 từ để đảm bảo tính chơi được
        valid_lengths = [l for l, words in pool_map.items() if len(words) >= 5]
        
        # Nếu data ít quá (fallback), chấp nhận tất cả
        if not valid_lengths: valid_lengths = list(pool_map.keys()) if pool_map else [5]
        
        chosen_len = random.choice(valid_lengths)
        candidates_pool = pool_map.get(chosen_len, ALL_WORDS_VI)
        
        if not candidates_pool: # Fallback cực đoan
            candidates_pool = ["thanh", "nhung"]
            chosen_len = 5
            
        answer = random.choice(candidates_pool)
        
        # AI dùng chung từ điển với người (lọc theo độ dài)
        ai_candidates = [w for w in candidates_pool if len(w) == chosen_len]

    user_token = str(uuid.uuid4())
    ACTIVE_GAMES[user_token] = {
        "username": username,
        "mode": mode,
        "strict": strict,
        "answer": answer,
        "history": [],
        "hint_level": 0,
        "ai_solver": WordleAISolver(ai_candidates, mode, strict)
    }

    print(f"--> New Game [{mode}]: {answer} (Len: {len(answer)})")

    return jsonify({
        "status": "ok",
        "token": user_token,
        "length": len(answer),
        "max_turns": MAX_TURNS
    })

@app.route("/guess", methods=["POST"])
def guess():
    data = request.json
    token = data.get("token")
    guess_word = data.get("guess")
    if not token or token not in ACTIVE_GAMES: return jsonify({"error": "Game not found"}), 400
    
    game = ACTIVE_GAMES[token]
    if len(guess_word) != len(game["answer"]):
        return jsonify({"error": f"Độ dài không đúng"}), 400

    feedback = evaluate(game["answer"], guess_word, game["mode"], game["strict"])
    game["history"].append((guess_word, feedback))
    
    if game["ai_solver"]: game["ai_solver"].update_candidates(guess_word, feedback)
    
    win = all(c == "green" for c in feedback)
    lose = len(game["history"]) >= MAX_TURNS and not win
    if win or lose: save_game(game["username"], game["mode"], game["answer"], len(game["history"]), 1 if win else 0, game["history"])

    return jsonify({"guess": guess_word, "feedback": feedback, "win": win, "lose": lose, "turn": len(game["history"]), "answer": game["answer"] if lose else None})

@app.route("/get_hint", methods=["POST"])
def get_hint():
    data = request.json
    token = data.get("token")
    if token in ACTIVE_GAMES: return jsonify({"hint": ai_generate_hint(ACTIVE_GAMES[token])})
    return jsonify({"error": "Game not found"}), 400

@app.route("/ai_auto_move", methods=["POST"])
def ai_auto_move():
    data = request.json
    token = data.get("token")
    if token not in ACTIVE_GAMES: return jsonify({"error": "Game not found"}), 400
    game = ACTIVE_GAMES[token]
    ai = game["ai_solver"]
    
    # Truyền số turn để AI biết đường tính (logic random lượt đầu)
    # Lưu ý: ai_solver.py cần hỗ trợ tham số turn_count trong choose_guess
    # Nếu ai_solver cũ không hỗ trợ, nó sẽ bỏ qua tham số này hoặc lỗi
    # Giả định ai_solver đã được cập nhật ở bước trước
    try:
        best_guess = ai.choose_guess(len(game["history"]))
    except TypeError:
        best_guess = ai.choose_guess() # Fallback cho bản cũ
    
    if not best_guess: return jsonify({"error": "AI bó tay"}), 400

    answer = game["answer"]
    feedback = evaluate(answer, best_guess, game["mode"], game["strict"])
    game["history"].append((best_guess, feedback))
    ai.update_candidates(best_guess, feedback)
    win = all(c == "green" for c in feedback)
    lose = len(game["history"]) >= MAX_TURNS and not win
    if win or lose: save_game(game["username"], game["mode"], answer, len(game["history"]), 1 if win else 0, game["history"])

    return jsonify({"guess": best_guess, "feedback": feedback, "win": win, "lose": lose, "turn": len(game["history"]), "answer": answer if lose else None, "remaining_candidates": len(ai.candidates)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)