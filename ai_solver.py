import random

class WordleAISolver:
    def __init__(self, words, mode="vi", strict=False):
        self.candidates = list(words)
        self.mode = mode
        self.strict = strict
        # Lưu lại tổng số từ ban đầu để biết quy mô pool
        self.initial_pool_size = len(words)

    def choose_guess(self, turn_count=0):
        if not self.candidates:
            return None
        
        # Nếu chỉ còn 1 từ thì bắt buộc chọn
        if len(self.candidates) == 1:
            return self.candidates[0]

        # --- LOGIC LƯỢT ĐẦU TIÊN (Tránh cheat) ---
        # Nếu là lượt 0 và pool từ vựng lớn (>10), AI không nên cố đoán trúng ngay.
        # Mà nên chọn từ có độ phủ cao nhất để loại trừ.
        # Ta sẽ dùng logic Frequency nhưng thêm Random nhẹ để nó không cứng nhắc.
        
        # 1. Tính tần suất
        char_freq = {}
        for word in self.candidates:
            for char in set(word): 
                char_freq[char] = char_freq.get(char, 0) + 1

        # 2. Tính điểm
        scored_words = []
        for word in self.candidates:
            unique_chars = set(word)
            score = sum(char_freq.get(c, 0) for c in unique_chars)
            # Thêm một chút nhiễu ngẫu nhiên (0-5% điểm) để AI không luôn chọn 1 từ duy nhất
            random_noise = random.uniform(0, score * 0.05)
            scored_words.append((score + random_noise, word))

        # 3. Sắp xếp điểm cao xuống thấp
        scored_words.sort(key=lambda x: x[0], reverse=True)
        
        # Nếu là lượt đầu và có nhiều lựa chọn, lấy ngẫu nhiên trong Top 5 từ tốt nhất
        # Để AI mỗi ván mở bài một kiểu khác nhau
        if turn_count == 0 and len(scored_words) >= 5:
            top_5 = scored_words[:5]
            return random.choice(top_5)[1]
            
        # Các lượt sau: Chọn từ điểm cao nhất
        return scored_words[0][1]

    def update_candidates(self, guess, feedback):
        new_candidates = []
        for word in self.candidates:
            ok = True
            for i, (char_guess, color) in enumerate(zip(guess, feedback)):
                if color == "green":
                    if word[i] != char_guess:
                        ok = False; break
                elif color == "yellow":
                    if char_guess not in word or word[i] == char_guess:
                        ok = False; break
                elif color == "gray":
                    if char_guess in word:
                         if guess.count(char_guess) == 1:
                             ok = False; break
            if ok:
                new_candidates.append(word)
        self.candidates = new_candidates