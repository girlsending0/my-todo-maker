const API = '/api/todos';
let currentYear, currentMonth, selectedDate;

function init() {
    const now = new Date();
    currentYear = now.getFullYear();
    currentMonth = now.getMonth();
    selectedDate = formatDate(now);
    renderCalendar();
    loadTodos(selectedDate);
}

function formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function todayStr() { return formatDate(new Date()); }

async function fetchTodosForMonth() {
    const start = new Date(currentYear, currentMonth, 1);
    const end = new Date(currentYear, currentMonth + 1, 0);
    const params = new URLSearchParams({
        start: formatDate(start),
        end: formatDate(end),
    });
    const resp = await fetch(`${API}?${params}`);
    return resp.json();
}

async function renderCalendar() {
    const todos = await fetchTodosForMonth();
    const todoMap = {};
    todos.forEach(t => {
        if (!todoMap[t.due_date]) todoMap[t.due_date] = [];
        todoMap[t.due_date].push(t);
    });

    const cal = document.getElementById('calendar');
    const label = document.getElementById('month-label');
    const monthNames = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'];
    label.textContent = `${currentYear}년 ${monthNames[currentMonth]}`;

    cal.innerHTML = '';

    // Day headers
    ['일','월','화','수','목','금','토'].forEach(d => {
        const el = document.createElement('div');
        el.className = 'day-header';
        el.textContent = d;
        cal.appendChild(el);
    });

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const prevDays = new Date(currentYear, currentMonth, 0).getDate();

    // Previous month
    for (let i = firstDay - 1; i >= 0; i--) {
        const el = createDayEl(prevDays - i, true, null);
        cal.appendChild(el);
    }

    // Current month
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${currentYear}-${String(currentMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const el = createDayEl(d, false, todoMap[dateStr] || []);
        if (dateStr === todayStr()) el.classList.add('today');
        if (dateStr === selectedDate) el.classList.add('selected');
        el.addEventListener('click', () => {
            selectedDate = dateStr;
            document.querySelectorAll('.day.selected').forEach(e => e.classList.remove('selected'));
            el.classList.add('selected');
            loadTodos(dateStr);
        });
        cal.appendChild(el);
    }

    // Next month fill
    const totalCells = firstDay + daysInMonth;
    const remaining = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let i = 1; i <= remaining; i++) {
        const el = createDayEl(i, true, null);
        cal.appendChild(el);
    }
}

function createDayEl(num, isOther, todos) {
    const el = document.createElement('div');
    el.className = 'day' + (isOther ? ' other-month' : '');

    const dateNum = document.createElement('div');
    dateNum.className = 'date-num';
    dateNum.textContent = num;
    el.appendChild(dateNum);

    if (todos && todos.length > 0) {
        const dots = document.createElement('div');
        dots.className = 'dot-container';
        todos.forEach(t => {
            const dot = document.createElement('div');
            dot.className = 'dot' + (t.is_completed ? ' done' : '');
            dots.appendChild(dot);
        });
        el.appendChild(dots);
    }

    return el;
}

async function loadTodos(dateStr) {
    const resp = await fetch(`${API}?date=${dateStr}`);
    const todos = await resp.json();

    const panel = document.getElementById('todo-panel');
    const d = new Date(dateStr + 'T00:00:00');
    const dayNames = ['일','월','화','수','목','금','토'];
    const title = `${d.getMonth()+1}/${d.getDate()} (${dayNames[d.getDay()]})`;

    let html = `<h2>${title}</h2>`;

    if (todos.length === 0) {
        html += '<p class="empty">등록된 할 일이 없습니다.</p>';
    } else {
        todos.forEach(t => {
            const checked = t.is_completed ? 'checked' : '';
            const cls = t.is_completed ? 'completed' : '';
            const timeStr = t.due_time ? t.due_time.substring(0, 5) : '';
            html += `
                <div class="todo-item">
                    <input type="checkbox" ${checked} onchange="toggleTodo(${t.id}, this.checked)">
                    <span class="title ${cls}">${t.title}</span>
                    ${timeStr ? `<span class="time">${timeStr}</span>` : ''}
                    <button class="delete-btn" onclick="removeTodo(${t.id})">×</button>
                </div>
            `;
        });
    }

    html += `
        <div class="add-form">
            <input type="text" id="new-todo" placeholder="할 일 입력..." onkeydown="if(event.key==='Enter')addTodo()">
            <button onclick="addTodo()">추가</button>
        </div>
    `;

    panel.innerHTML = html;
}

async function toggleTodo(id, completed) {
    await fetch(`${API}/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_completed: completed }),
    });
    renderCalendar();
    loadTodos(selectedDate);
}

async function removeTodo(id) {
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    renderCalendar();
    loadTodos(selectedDate);
}

async function addTodo() {
    const input = document.getElementById('new-todo');
    const title = input.value.trim();
    if (!title) return;

    await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, due_date: selectedDate }),
    });

    input.value = '';
    renderCalendar();
    loadTodos(selectedDate);
}

function prevMonth() {
    currentMonth--;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    renderCalendar();
}

function nextMonth() {
    currentMonth++;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    renderCalendar();
}

document.addEventListener('DOMContentLoaded', init);
