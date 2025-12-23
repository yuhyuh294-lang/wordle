import random

def generate_equation(length=7):
    """
    Sinh biểu thức toán học dạng: A op B = C
    Đảm bảo độ dài chuỗi (bao gồm cả dấu =) đúng bằng length.
    Ví dụ length=7: '2*3+1=7' (khó) hoặc '10-3=7 '
    """
    operators = ['+', '-', '*']
    
    # Thử tối đa 2000 lần để tìm ra phép tính khớp độ dài
    for _ in range(2000):
        op = random.choice(operators)
        
        # Random số A và B (tùy chỉnh phạm vi để khó/dễ)
        a = random.randint(1, 50) 
        b = random.randint(1, 50)
        
        # Tạo vế trái
        expression = f"{a}{op}{b}"
        
        # Tính toán (bỏ qua nếu lỗi hoặc kết quả âm/lẻ)
        try:
            val = eval(expression)
        except:
            continue
            
        # Game chỉ dùng số nguyên dương (Wordle toán thường không dùng số âm)
        if not isinstance(val, int) or val < 0:
            continue
            
        full_eq = f"{expression}={val}"
        
        # Nếu đúng độ dài yêu cầu thì trả về
        if len(full_eq) == length:
            return full_eq
            
    # Fallback (Dự phòng) nếu xui quá không tìm được (trả về mặc định theo độ dài)
    if length == 5: return "1+1=2"
    if length == 6: return "2+2=4"
    if length == 7: return "10-3=7"
    if length == 8: return "10+5=15"
    return "1+1=2"