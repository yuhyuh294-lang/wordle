const API_URL = "";

let currentState = {
    token: null,
    mode: 'vi',
    length: 5,
    maxTurns: 6,
    currentRow: 0,
    currentTile: 0,
    isGameOver: false,
    guesses: [[]], 
};

const KEYS_VI = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
const KEYS_MATH = ["1234567890", "+-*/="];

const TELEX_MAP = {
    'a': { 's': 'á', 'f': 'à', 'r': 'ả', 'x': 'ã', 'j': 'ạ', 'w': 'ă', 'a': 'â' },
    'e': { 's': 'é', 'f': 'è', 'r': 'ẻ', 'x': 'ẽ', 'j': 'ẹ', 'e': 'ê' },
    'o': { 's': 'ó', 'f': 'ò', 'r': 'ỏ', 'x': 'õ', 'j': 'ọ', 'w': 'ơ', 'o': 'ô' },
    'u': { 's': 'ú', 'f': 'ù', 'r': 'ủ', 'x': 'ũ', 'j': 'ụ', 'w': 'ư' },
    'i': { 's': 'í', 'f': 'ì', 'r': 'ỉ', 'x': 'ĩ', 'j': 'ị' },
    'y': { 's': 'ý', 'f': 'ỳ', 'r': 'ỷ', 'x': 'ỹ', 'j': 'ỵ' },
    'd': { 'd': 'đ' },
    'â': { 's': 'ấ', 'f': 'ầ', 'r': 'ẩ', 'x': 'ẫ', 'j': 'ậ' },
    'ă': { 's': 'ắ', 'f': 'ằ', 'r': 'ẳ', 'x': 'ẵ', 'j': 'ặ' },
    'ê': { 's': 'ế', 'f': 'ề', 'r': 'ể', 'x': 'ễ', 'j': 'ệ' },
    'ô': { 's': 'ố', 'f': 'ồ', 'r': 'ổ', 'x': 'ỗ', 'j': 'ộ' },
    'ơ': { 's': 'ớ', 'f': 'ờ', 'r': 'ở', 'x': 'ỡ', 'j': 'ợ' },
    'ư': { 's': 'ứ', 'f': 'ừ', 'r': 'ử', 'x': 'ữ', 'j': 'ự' },
};

// --- 1. KHỞI TẠO GAME ---
function initGame(mode) {
    // FIX BUG: Bỏ focus khỏi nút vừa bấm để Enter không kích hoạt lại nó
    if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
    }

    currentState.mode = mode;
    document.getElementById("mode-badge").innerText = mode === 'math' ? "TOÁN HỌC" : "TIẾNG VIỆT";
    document.getElementById("message").innerText = "Đang tải...";
    
    // Reset bàn phím
    document.querySelectorAll(".key").forEach(k => k.style.backgroundColor = "");

    fetch(`${API_URL}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "Player1", mode: mode })
    })
    .then(res => res.json())
    .then(data => {
        currentState.token = data.token;
        currentState.length = data.length;
        currentState.maxTurns = data.max_turns;
        currentState.currentRow = 0;
        currentState.isGameOver = false;
        currentState.guesses = Array(data.max_turns).fill(null).map(() => []);
        
        createBoard();
        createKeyboard();
        document.getElementById("message").innerText = "";
    })
    .catch(err => alert("Lỗi kết nối Server! Bạn đã chạy 'python backend.py' chưa?"));
}

function createBoard() {
    const board = document.getElementById("game-board");
    board.innerHTML = "";
    board.style.gridTemplateColumns = `repeat(${currentState.length}, 1fr)`;
    const tileSize = currentState.length > 8 ? "40px" : "55px";

    for (let i = 0; i < currentState.maxTurns * currentState.length; i++) {
        const tile = document.createElement("div");
        tile.className = "tile";
        tile.id = `tile-${i}`;
        tile.style.width = tileSize;
        tile.style.height = tileSize;
        tile.style.lineHeight = tileSize;
        board.appendChild(tile);
    }
}

function createKeyboard() {
    const container = document.getElementById("keyboard-container");
    container.innerHTML = "";
    const layout = currentState.mode === 'math' ? KEYS_MATH : KEYS_VI;

    layout.forEach((rowString) => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "kb-row";
        rowString.split("").forEach(char => {
            const btn = document.createElement("div");
            btn.className = "key";
            btn.textContent = char;
            btn.dataset.key = char;
            btn.onclick = () => handleInput(char);
            rowDiv.appendChild(btn);
        });
        container.appendChild(rowDiv);
    });

    const funcRow = document.createElement("div");
    funcRow.className = "kb-row";
    
    const btnEnter = document.createElement("div");
    btnEnter.className = "key key-big";
    btnEnter.textContent = "ENTER";
    btnEnter.onclick = () => submitGuess();
    
    const btnDel = document.createElement("div");
    btnDel.className = "key key-big";
    btnDel.textContent = "⌫";
    btnDel.onclick = () => handleDelete();

    funcRow.appendChild(btnEnter);
    funcRow.appendChild(btnDel);
    container.appendChild(funcRow);
}

// --- 2. XỬ LÝ NHẬP LIỆU ---
function handleInput(key) {
    if (currentState.isGameOver) return;
    let row = currentState.guesses[currentState.currentRow];
    key = key.toLowerCase();

    // Logic Telex
    if (currentState.mode === 'vi' && row.length > 0) {
        const lastIndex = row.length - 1;
        const lastChar = row[lastIndex];
        if (TELEX_MAP[lastChar] && TELEX_MAP[lastChar][key]) {
            const newChar = TELEX_MAP[lastChar][key];
            row[lastIndex] = newChar;
            updateTile(currentState.currentRow, lastIndex, newChar);
            return;
        }
    }

    if (row.length < currentState.length) {
        if (key.length === 1 && key.match(/[a-z0-9+\-*=]/i)) {
            row.push(key);
            updateTile(currentState.currentRow, row.length - 1, key);
        }
    }
}

function handleDelete() {
    if (currentState.isGameOver) return;
    const row = currentState.guesses[currentState.currentRow];
    if (row.length > 0) {
        row.pop();
        updateTile(currentState.currentRow, row.length, ""); 
    }
}

function updateTile(row, col, val) {
    const tile = document.getElementById(`tile-${row * currentState.length + col}`);
    tile.textContent = val;
    tile.classList.add("pulse");
    setTimeout(() => tile.classList.remove("pulse"), 100);
}

// --- 3. SỰ KIỆN BÀN PHÍM (ĐÃ SỬA LỖI ENTER) ---
document.addEventListener("keydown", (e) => {
    // QUAN TRỌNG: Ngăn chặn hành vi mặc định của Enter (tránh click vào nút Start game)
    if (e.key === "Enter") {
        e.preventDefault(); 
        submitGuess();
    }
    else if (e.key === "Backspace") {
        handleDelete();
    }
    // Chỉ nhận phím ký tự đơn
    else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
        handleInput(e.key);
    }
});

// --- 4. CÁC HÀM GAME ---
function submitGuess() {
    if (currentState.isGameOver) return;
    const guessArr = currentState.guesses[currentState.currentRow];
    
    if (guessArr.length !== currentState.length) {
        showMessage("Chưa đủ ký tự!");
        shakeRow();
        return;
    }
    
    const guessStr = guessArr.join("");
    
    fetch(`${API_URL}/guess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: currentState.token, guess: guessStr })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showMessage(data.error);
            shakeRow();
            return;
        }
        handleGameResponse(data);
    });
}

function autoPlayAI() {
    if (currentState.isGameOver || !currentState.token) return;
    showMessage("🤖 AI đang tính toán...");
    
    fetch(`${API_URL}/ai_auto_move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: currentState.token })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) { showMessage(data.error); return; }

        const rowIdx = data.turn - 1;
        currentState.currentRow = rowIdx;
        const guessChars = data.guess.split("");
        currentState.guesses[rowIdx] = guessChars;
        
        guessChars.forEach((char, i) => {
            const tile = document.getElementById(`tile-${rowIdx * currentState.length + i}`);
            tile.textContent = char;
        });

        handleGameResponse(data);
    });
}

function handleGameResponse(data) {
    const rowIdx = data.turn - 1;
    animateFlip(data.feedback, rowIdx);
    
    if (data.win) {
        setTimeout(() => showMessage("🏆 CHIẾN THẮNG TUYỆT ĐỐI!"), 1500);
        currentState.isGameOver = true;
    } else if (data.lose) {
        setTimeout(() => showMessage(`💀 THUA RỒI! ĐÁP ÁN: ${data.answer}`), 1500);
        currentState.isGameOver = true;
    } else {
        currentState.currentRow = data.turn;
    }
}

function getHint() {
    if(!currentState.token || currentState.isGameOver) return;
    fetch(`${API_URL}/get_hint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: currentState.token })
    })
    .then(res => res.json())
    .then(data => alert(data.hint));
}

function animateFlip(feedback, rowIdx) {
    feedback.forEach((color, i) => {
        setTimeout(() => {
            const tileIdx = rowIdx * currentState.length + i;
            const tile = document.getElementById(`tile-${tileIdx}`);
            tile.style.setProperty("--color", getColorCode(color));
            tile.classList.add("flip");
            updateKeyColor(currentState.guesses[rowIdx][i], color);
        }, i * 300);
    });
}

function updateKeyColor(char, status) {
    if(!char) return;
    const baseChar = char.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace("đ", "d").toLowerCase();
    
    const keys = document.querySelectorAll(".key");
    keys.forEach(key => {
        if (key.dataset.key === baseChar) {
            const newColor = getColorCode(status);
            // Logic ưu tiên màu: Green > Yellow > Gray
            if (newColor === "#538d4e") { 
                key.style.backgroundColor = newColor;
            } else if (newColor === "#b59f3b" && key.style.backgroundColor !== "rgb(83, 141, 78)") {
                key.style.backgroundColor = newColor;
            } else if (key.style.backgroundColor === "") {
                key.style.backgroundColor = newColor;
            }
        }
    });
}

function getColorCode(status) {
    if (status === "green") return "#538d4e";
    if (status === "yellow") return "#b59f3b";
    return "#3a3a3c";
}

function showMessage(msg) { document.getElementById("message").innerText = msg; }
function shakeRow() {
    const start = currentState.currentRow * currentState.length;
    for(let i=0; i < currentState.length; i++) {
        const tile = document.getElementById(`tile-${start + i}`);
        tile.classList.add("shake");
        setTimeout(() => tile.classList.remove("shake"), 500);
    }
}

// Bắt đầu game mặc định
initGame('vi');