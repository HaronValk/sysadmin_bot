"""Mini App на Flask."""

import threading, re
from flask import Flask, abort, request, jsonify
from db import get_cached_lesson
from lessons_loader import LESSONS, TOTAL_LESSONS
from ai_client import ask_ai

web_app = Flask(__name__)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Урок {{lid}} - {{topic}}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
        :root {
            --bg: #0d0f1a;
            --surface: #151829;
            --surface2: #1c2035;
            --text: #e0e2f0;
            --text2: #a0a5c0;
            --neon-cyan: #00f0ff;
            --neon-pink: #ff00aa;
            --neon-purple: #b300ff;
            --neon-green: #00ff88;
            --neon-yellow: #ffe600;
            --code-bg: #0a0c16;
            --border: #2a2f45;
            --shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            padding: 20px 16px 32px;
            min-height: 100vh;
            max-width: 800px;
            margin: 0 auto;
            background-image:
                radial-gradient(ellipse at 20% 20%, rgba(0,240,255,0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(255,0,170,0.04) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(179,0,255,0.03) 0%, transparent 50%);
        }
        h1 {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }
        h2 {
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--neon-cyan);
            margin: 28px 0 12px;
            padding-left: 12px;
            border-left: 3px solid var(--neon-cyan);
        }
        h3 {
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--neon-pink);
            margin: 20px 0 8px;
        }
        .summary {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0 24px;
            color: var(--text2);
            font-style: italic;
            box-shadow: var(--shadow);
            border-left: 3px solid var(--neon-purple);
        }
        .btn-row {
            display: flex;
            gap: 8px;
            margin: 16px 0;
            flex-wrap: wrap;
        }
        .btn {
            background: var(--surface);
            color: var(--neon-cyan);
            border: 1px solid var(--neon-cyan);
            padding: 10px 16px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
            text-align: center;
            flex: 1;
            min-width: 100px;
        }
        .btn:hover {
            background: var(--neon-cyan);
            color: var(--bg);
            box-shadow: 0 0 15px rgba(0,240,255,0.4);
        }
        p { margin-bottom: 12px; }
        ul, ol { margin: 12px 0 12px 20px; padding-left: 16px; list-style-position: outside; }
        li { margin-bottom: 6px; }
        strong { color: var(--neon-green); font-weight: 700; }
        pre {
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            position: relative;
            overflow-x: auto;
            margin: 16px 0;
            box-shadow: var(--shadow);
            border-left: 3px solid var(--neon-cyan);
        }
        code {
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            padding-right: 40px;
        }
        .copy-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 32px;
            height: 32px;
            background: var(--surface2);
            color: var(--neon-cyan);
            border: 1px solid var(--neon-cyan);
            border-radius: 50%;
            cursor: pointer;
            font-size: 1rem;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .copy-btn:hover {
            background: var(--neon-cyan);
            color: var(--bg);
            box-shadow: 0 0 12px rgba(0,240,255,0.4);
        }
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 100;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: var(--surface);
            border: 1px solid var(--neon-cyan);
            border-radius: 16px;
            padding: 24px;
            max-width: 600px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 0 40px rgba(0,240,255,0.3);
        }
        .modal-content h3 { margin-top: 0; }
        .close-btn {
            float: right;
            background: none;
            border: none;
            color: var(--neon-pink);
            font-size: 1.5rem;
            cursor: pointer;
        }
        .ai-input {
            width: 100%;
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            margin: 12px 0;
            resize: vertical;
            min-height: 80px;
        }
        .ai-answer {
            background: var(--code-bg);
            border: 1px solid var(--neon-green);
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
            color: var(--text);
            white-space: pre-wrap;
        }
        .project-progress {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 16px 0;
            color: var(--neon-cyan);
            font-weight: 600;
        }
        .progress-bar {
            flex: 1;
            height: 8px;
            background: var(--code-bg);
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--neon-cyan), var(--neon-green));
            border-radius: 4px;
            transition: width 0.3s;
        }
        .project-nav {
            display: flex;
            gap: 8px;
            margin: 16px 0;
        }
        .project-nav a {
            flex: 1;
            text-align: center;
            background: var(--surface);
            color: var(--neon-yellow);
            border: 1px solid var(--neon-yellow);
            padding: 8px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .nav {
            display: flex;
            gap: 12px;
            margin-top: 32px;
            flex-wrap: wrap;
        }
        .nav a, .nav span {
            display: inline-block;
            flex: 1;
            min-width: 100px;
            padding: 12px 16px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            text-align: center;
            transition: all 0.25s;
            letter-spacing: 0.3px;
            font-size: 0.95rem;
        }
        .nav a {
            background: var(--surface);
            color: var(--neon-cyan);
            border: 1px solid var(--neon-cyan);
            box-shadow: 0 0 15px rgba(0,240,255,0.15);
        }
        .nav a:hover {
            background: var(--neon-cyan);
            color: var(--bg);
            box-shadow: 0 0 30px rgba(0,240,255,0.4);
            transform: translateY(-2px);
        }
        .nav span.disabled {
            background: var(--surface);
            color: #4a4f66;
            border: 1px solid #2a2f45;
        }
        @media (max-width: 480px) {
            body { padding: 14px 10px 24px; }
            h1 { font-size: 1.5rem; }
            h2 { font-size: 1.2rem; }
            pre { padding: 10px; }
            .copy-btn { width: 28px; height: 28px; font-size: 0.9rem; top: 4px; right: 4px; }
            .nav a, .nav span { padding: 10px 12px; font-size: 0.85rem; }
        }
    </style>
</head>
<body>
    <h1>Урок {{lid}}: {{topic}}</h1>
    <div class="summary">{{summary}}</div>
    
    <div class="btn-row">
        <button class="btn" onclick="openPractice()">📝 Задание</button>
        <a class="btn" href="/project/{{lid}}" style="text-decoration:none">🏗️ Проект</a>
        <button class="btn" onclick="openAI()">🤖 Спросить ИИ</button>
    </div>
    
    <div id="content">{{content}}</div>

    <div class="nav">
        {{prev_link}}
        {{next_link}}
    </div>

    <div id="practiceModal" class="modal">
        <div class="modal-content">
            <button class="close-btn" onclick="closeModal('practiceModal')">✕</button>
            <h3>📝 Практическое задание</h3>
            <p>{{practice_text}}</p>
        </div>
    </div>

    <div id="aiModal" class="modal">
        <div class="modal-content">
            <button class="close-btn" onclick="closeModal('aiModal')">✕</button>
            <h3>🤖 Задай вопрос ИИ по уроку {{lid}}</h3>
            <textarea class="ai-input" id="aiQuestion" placeholder="Введи вопрос..."></textarea>
            <button class="btn" onclick="askAI()" style="width:100%">Спросить</button>
            <div class="ai-answer" id="aiAnswer" style="display:none"></div>
        </div>
    </div>

    <script>
        hljs.highlightAll();
        
        document.querySelectorAll('pre').forEach(pre => {
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.textContent = '📋';
            btn.title = 'Копировать код';
            btn.addEventListener('click', () => {
                const code = pre.querySelector('code') || pre;
                navigator.clipboard.writeText(code.textContent).then(() => {
                    btn.textContent = '✅';
                    setTimeout(() => btn.textContent = '📋', 2000);
                });
            });
            pre.style.position = 'relative';
            pre.appendChild(btn);
        });
        
        function openPractice() { document.getElementById('practiceModal').classList.add('active'); }
        function openAI() { document.getElementById('aiModal').classList.add('active'); }
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        
        async function askAI() {
            const question = document.getElementById('aiQuestion').value;
            if (!question) return;
            const answerDiv = document.getElementById('aiAnswer');
            answerDiv.style.display = 'block';
            answerDiv.textContent = 'Думаю...';
            const lid = {{lid}};
            const res = await fetch('/api/ask?lid=' + lid + '&question=' + encodeURIComponent(question));
            const data = await res.json();
            answerDiv.textContent = data.answer;
        }
        
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.classList.remove('active');
            });
        });
        
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.BackButton.show();
            window.Telegram.WebApp.BackButton.onClick(() => window.history.back());
            window.Telegram.WebApp.ready();
        }
    </script>
</body>
</html>"""

PROJECT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Проект — Урок {{lid}}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
        :root {
            --bg: #0d0f1a;
            --surface: #151829;
            --surface2: #1c2035;
            --text: #e0e2f0;
            --text2: #a0a5c0;
            --neon-cyan: #00f0ff;
            --neon-pink: #ff00aa;
            --neon-purple: #b300ff;
            --neon-green: #00ff88;
            --neon-yellow: #ffe600;
            --code-bg: #0a0c16;
            --border: #2a2f45;
            --shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            padding: 20px 16px 32px;
            min-height: 100vh;
            max-width: 800px;
            margin: 0 auto;
            background-image:
                radial-gradient(ellipse at 20% 20%, rgba(0,240,255,0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(255,0,170,0.04) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(179,0,255,0.03) 0%, transparent 50%);
        }
        h1 {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--neon-yellow), var(--neon-pink));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        h2 {
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--neon-cyan);
            margin: 28px 0 12px;
            padding-left: 12px;
            border-left: 3px solid var(--neon-cyan);
        }
        h3 {
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--neon-pink);
            margin: 20px 0 8px;
        }
        .project-progress {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 16px 0;
            color: var(--neon-cyan);
            font-weight: 600;
        }
        .progress-bar {
            flex: 1;
            height: 8px;
            background: var(--code-bg);
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--neon-cyan), var(--neon-green));
            border-radius: 4px;
        }
        p { margin-bottom: 12px; }
        ul, ol { margin: 12px 0 12px 20px; padding-left: 16px; list-style-position: outside; }
        li { margin-bottom: 6px; }
        strong { color: var(--neon-green); font-weight: 700; }
        pre {
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            position: relative;
            overflow-x: auto;
            margin: 16px 0;
            box-shadow: var(--shadow);
            border-left: 3px solid var(--neon-cyan);
        }
        code {
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            padding-right: 40px;
        }
        .copy-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 32px;
            height: 32px;
            background: var(--surface2);
            color: var(--neon-cyan);
            border: 1px solid var(--neon-cyan);
            border-radius: 50%;
            cursor: pointer;
            font-size: 1rem;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .project-nav {
            display: flex;
            gap: 8px;
            margin: 16px 0;
            flex-wrap: wrap;
        }
        .project-nav a {
            flex: 1;
            text-align: center;
            background: var(--surface);
            color: var(--neon-yellow);
            border: 1px solid var(--neon-yellow);
            padding: 10px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            min-width: 100px;
        }
        .project-nav a:hover {
            background: var(--neon-yellow);
            color: var(--bg);
        }
        .nav {
            display: flex;
            gap: 12px;
            margin-top: 32px;
            flex-wrap: wrap;
        }
        .nav a, .nav span {
            display: inline-block;
            flex: 1;
            min-width: 100px;
            padding: 12px 16px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            text-align: center;
            transition: all 0.25s;
            letter-spacing: 0.3px;
            font-size: 0.95rem;
        }
        .nav a {
            background: var(--surface);
            color: var(--neon-cyan);
            border: 1px solid var(--neon-cyan);
            box-shadow: 0 0 15px rgba(0,240,255,0.15);
        }
        .nav a:hover {
            background: var(--neon-cyan);
            color: var(--bg);
            box-shadow: 0 0 30px rgba(0,240,255,0.4);
            transform: translateY(-2px);
        }
        .nav span.disabled {
            background: var(--surface);
            color: #4a4f66;
            border: 1px solid #2a2f45;
        }
        @media (max-width: 480px) {
            body { padding: 14px 10px 24px; }
            h1 { font-size: 1.5rem; }
            pre { padding: 10px; }
            .copy-btn { width: 28px; height: 28px; font-size: 0.9rem; top: 4px; right: 4px; }
        }
    </style>
</head>
<body>
    <h1>🏗️ Сквозной проект</h1>
    <div class="project-progress">
        <span>Прогресс:</span>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{progress_percent}}%"></div>
        </div>
        <span>{{progress_done}}/{{progress_total}}</span>
    </div>
    
    <div class="project-nav">
        {{prev_project_link}}
        <a href="/lesson/{{lid}}">📖 К уроку</a>
        {{next_project_link}}
    </div>
    
    <h2>Шаг урока {{lid}}: {{topic}}</h2>
    <div id="content">{{project_step}}</div>

    <div class="nav">
        {{prev_link}}
        {{next_link}}
    </div>

    <script>
        hljs.highlightAll();
        document.querySelectorAll('pre').forEach(pre => {
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.textContent = '📋';
            btn.title = 'Копировать код';
            btn.addEventListener('click', () => {
                const code = pre.querySelector('code') || pre;
                navigator.clipboard.writeText(code.textContent).then(() => {
                    btn.textContent = '✅';
                    setTimeout(() => btn.textContent = '📋', 2000);
                });
            });
            pre.style.position = 'relative';
            pre.appendChild(btn);
        });
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.BackButton.show();
            window.Telegram.WebApp.BackButton.onClick(() => window.history.back());
            window.Telegram.WebApp.ready();
        }
    </script>
</body>
</html>"""


@web_app.route("/lesson/<int:lid>")
def lesson_page(lid):
    content = get_cached_lesson(lid)
    if not content:
        abort(404)
    lesson = LESSONS[lid]
    prev_id = lid - 1 if lid > 1 else None
    next_id = lid + 1 if lid < TOTAL_LESSONS else None
    prev_link = (
        f'<a href="/lesson/{prev_id}">⬅️ Назад</a>'
        if prev_id
        else '<span class="disabled">⬅️ Назад</span>'
    )
    next_link = (
        f'<a href="/lesson/{next_id}">Вперёд ➡️</a>'
        if next_id
        else '<span class="disabled">Вперёд ➡️</span>'
    )
    practice = lesson.get("practice", "Задание отсутствует.")

    html = TEMPLATE.replace("{{lid}}", str(lid))
    html = html.replace("{{topic}}", lesson["topic"])
    html = html.replace("{{summary}}", lesson["summary"])
    html = html.replace("{{content}}", content)
    html = html.replace("{{prev_link}}", prev_link)
    html = html.replace("{{next_link}}", next_link)
    html = html.replace("{{practice_text}}", practice)
    return html


@web_app.route("/project/<int:lid>")
def project_page(lid):
    lesson = LESSONS[lid]
    raw_step = (
        lesson.get("project_step_ru")
        or lesson.get("project_step_global")
        or "Для этого урока нет шага проекта."
    )

    # Разбиваем на блоки кода и обычный текст
    parts = re.split(r"(```.*?```)", raw_step, flags=re.DOTALL)
    formatted_parts = []
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            # Блок кода — оборачиваем в <pre><code>
            content = part[3:-3].strip()
            lines = content.split("\n", 1)
            if len(lines) > 1 and not lines[0].strip().startswith(" "):
                code = lines[1]
            else:
                code = content
            formatted_parts.append(f"<pre><code>{code}</code></pre>")
        else:
            # Обычный текст — преобразуем markdown в HTML
            text = part
            # Убираем первый заголовок ## Шаг X (дублируется с названием страницы)
            text = re.sub(
                r"^##\s*Шаг\s*\d+[.:]\s*.+?\n", "", text, count=1, flags=re.MULTILINE
            )
            # Заголовки ##
            text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
            # Жирный **текст**
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            # Списки (строки, начинающиеся с -)
            lines = text.split("\n")
            in_list = False
            result = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("- "):
                    if not in_list:
                        result.append("<ul>")
                        in_list = True
                    result.append(f"<li>{stripped[2:]}</li>")
                else:
                    if in_list:
                        result.append("</ul>")
                        in_list = False
                    result.append(line)
            if in_list:
                result.append("</ul>")
            text = "\n".join(result)
            # Переносы строк
            text = text.replace("\n", "<br>")
            formatted_parts.append(text)
    formatted_step = "".join(formatted_parts)

    # Прогресс и навигация
    total_steps = sum(
        1
        for l in LESSONS.values()
        if l.get("project_step_ru") or l.get("project_step_global")
    )
    completed = lid
    progress_percent = int(completed / total_steps * 100) if total_steps else 0

    prev_project = None
    next_project = None
    for i in range(lid - 1, 0, -1):
        if LESSONS[i].get("project_step_ru") or LESSONS[i].get("project_step_global"):
            prev_project = i
            break
    for i in range(lid + 1, TOTAL_LESSONS + 1):
        if LESSONS[i].get("project_step_ru") or LESSONS[i].get("project_step_global"):
            next_project = i
            break

    prev_project_link = (
        f'<a href="/project/{prev_project}">⬅️ Пред. шаг</a>'
        if prev_project
        else '<span class="disabled" style="flex:1;text-align:center;padding:10px;color:#4a4f66">⬅️ Пред. шаг</span>'
    )
    next_project_link = (
        f'<a href="/project/{next_project}">След. шаг ➡️</a>'
        if next_project
        else '<span class="disabled" style="flex:1;text-align:center;padding:10px;color:#4a4f66">След. шаг ➡️</span>'
    )

    prev_id = lid - 1 if lid > 1 else None
    next_id = lid + 1 if lid < TOTAL_LESSONS else None
    prev_link = f'<a href="/lesson/{prev_id}">⬅️ Назад к уроку</a>' if prev_id else ""
    next_link = f'<a href="/lesson/{next_id}">Вперёд к уроку ➡️</a>' if next_id else ""

    html = PROJECT_TEMPLATE.replace("{{lid}}", str(lid))
    html = html.replace("{{topic}}", lesson["topic"])
    html = html.replace("{{project_step}}", formatted_step)
    html = html.replace("{{progress_percent}}", str(progress_percent))
    html = html.replace("{{progress_done}}", str(completed))
    html = html.replace("{{progress_total}}", str(total_steps))
    html = html.replace("{{prev_project_link}}", prev_project_link)
    html = html.replace("{{next_project_link}}", next_project_link)
    html = html.replace("{{prev_link}}", prev_link)
    html = html.replace("{{next_link}}", next_link)
    return html


@web_app.route("/api/ask")
def api_ask():
    lid = int(request.args.get("lid", 0))
    question = request.args.get("question", "")
    if not question:
        return jsonify({"answer": "Вопрос не задан."})
    answer, _ = ask_ai(question, lid if lid > 0 else None)
    return jsonify({"answer": answer})


def start():
    threading.Thread(
        target=lambda: web_app.run(
            host="0.0.0.0", port=8080, debug=False, use_reloader=False
        ),
        daemon=True,
    ).start()
