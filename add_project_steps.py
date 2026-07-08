# add_project_steps.py
import json, time, os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

with open("lessons.json", "r", encoding="utf-8") as f:
    lessons = json.load(f)

SYSTEM_RU = """Ты — ведущий системный архитектор с 20-летним опытом работы в российских компаниях. 
Твоя задача — создать сквозной проект, который проведёт ученика от нуля до готовой корпоративной инфраструктуры, 
релевантной для РФ в 2026 году.

Проект называется "УралТехСервис" — это вымышленная российская компания из 60 сотрудников, занимающаяся промышленной автоматизацией. 
Ученик — единственный сисадмин, который строит IT-инфраструктуру компании с нуля.

Инфраструктура должна включать:
- Контроллер домена Active Directory на Windows Server 2025 (основной и резервный)
- Файловый сервер с DFS-R и теневыми копиями
- DHCP и DNS серверы (отказоустойчивая конфигурация)
- Сервер терминалов (RDS) для удалённых сотрудников
- Сервер с Astra Linux Special Edition (для соответствия требованиям импортозамещения)
- Docker-контейнеры для внутренних сервисов (использовать российские зеркала образов)
- Система мониторинга Zabbix 7 с дашбордами и оповещениями в Telegram
- VPN-сервер на базе WireGuard для защищённого удалённого доступа сотрудников
- Keycloak для единой аутентификации (замена Azure AD, который недоступен)
- Резервное копирование всей инфраструктуры на Yandex Cloud
- Антивирус Касперского (Kaspersky Endpoint Security) на всех Windows-машинах
- Почтовый сервер на базе Яндекс 360 для бизнеса
- Базовая интеграция с 1С:Предприятие (установка серверной части, настройка бэкапов)

Для каждого урока даётся ОДИН конкретный, детальный шаг проекта, связанный с темой урока. 
Шаг должен быть написан так, будто ты лично инструктируешь ученика:
- Начинай с глагола в повелительном наклонении: "Установи...", "Настрой...", "Создай..."
- Указывай точные параметры: IP-адреса (используй сеть 10.10.0.0/16), имена серверов, версии ПО
- Объясняй, зачем этот шаг нужен для компании "УралТехСервис"
- Добавляй конкретные команды PowerShell или bash, где это уместно
- Пиши так, чтобы шаг можно было проверить: "Убедись, что...", "Проверь командой..."
- Объём: 5-12 предложений
- На русском языке

Важно: шаги должны логически следовать друг за другом, образуя единую картину построения инфраструктуры с нуля."""

SYSTEM_GLOBAL = """Ты — ведущий системный архитектор с 20-летним опытом работы в международных компаниях. 
Твоя задача — создать сквозной проект, который проведёт ученика от нуля до готовой корпоративной инфраструктуры 
мирового уровня.

Проект называется "InfraProsper" — это вымышленная международная компания из 50 сотрудников, занимающаяся веб-разработкой. 
Ученик — DevOps/сисадмин, который строит IT-инфраструктуру компании с нуля, используя лучшие мировые практики.

Инфраструктура должна включать:
- Контроллер домена Active Directory на Windows Server 2025 (основной и резервный, с сайтами)
- Файловый сервер с DFS-R и теневыми копиями
- DHCP и DNS серверы (отказоустойчивая конфигурация)
- Сервер терминалов (RDS) с RemoteApps для разработчиков
- Сервер с Ubuntu 24.04 LTS для веб-приложений и инструментов DevOps
- Docker-контейнеры для микросервисов, оркестрация через Docker Compose
- Kubernetes кластер (Minikube или k3s) для тестовой среды
- Система мониторинга: Zabbix 7 + Grafana + Prometheus
- CI/CD пайплайн через GitHub Actions для автоматического деплоя
- VPN-сервер на базе WireGuard для защищённого удалённого доступа
- Azure AD (Entra ID) для гибридной аутентификации и синхронизации с локальной AD
- Резервное копирование всей инфраструктуры в Azure Backup
- Ansible для управления конфигурациями всех серверов
- Graylog для централизованного сбора и анализа логов
- Полная документация инфраструктуры в формате Markdown

Для каждого урока даётся ОДИН конкретный, детальный шаг проекта, связанный с темой урока. 
Шаг должен быть написан так, будто ты лично инструктируешь ученика:
- Начинай с глагола в повелительном наклонении: "Install...", "Configure...", "Deploy..."
- Указывай точные параметры: IP-адреса (используй сеть 172.16.0.0/16), имена серверов, версии ПО
- Объясняй, зачем этот шаг нужен для компании "InfraProsper"
- Добавляй конкретные команды PowerShell или bash, где это уместно
- Пиши так, чтобы шаг можно было проверить: "Verify that...", "Test using..."
- Объём: 5-12 предложений
- На русском языке

Важно: шаги должны логически следовать друг за другом, образуя единую картину построения инфраструктуры с нуля."""

skip_keywords = [
    "введение",
    "карьера",
    "резюме",
    "собеседование",
    "повторение",
    "mock",
    "Mock",
]

for i, lesson in enumerate(lessons, start=1):
    topic = lesson.get("topic", "")

    if any(kw in topic.lower() for kw in skip_keywords):
        continue

    has_ru = lesson.get("project_step_ru") and len(lesson["project_step_ru"]) > 100
    has_global = (
        lesson.get("project_step_global") and len(lesson["project_step_global"]) > 100
    )

    if has_ru and has_global:
        print(f"[{i}/{len(lessons)}] {topic} — оба шага уже есть")
        continue

    print(f"[{i}/{len(lessons)}] {topic} — генерирую...")

    lesson_text = f'Урок: "{topic}"\nОписание: {lesson.get("summary", "")}\nКлючевые слова: {", ".join(lesson.get("keywords", []))}'

    if not has_ru:
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_RU},
                    {"role": "user", "content": lesson_text},
                ],
                temperature=0.7,
                max_tokens=600,
            )
            lesson["project_step_ru"] = resp.choices[0].message.content.strip()
            print(f"  🇷🇺 РФ: {lesson['project_step_ru'][:80]}...")
        except Exception as e:
            print(f"  ❌ РФ ошибка: {e}")
        time.sleep(1)

    if not has_global:
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_GLOBAL},
                    {"role": "user", "content": lesson_text},
                ],
                temperature=0.7,
                max_tokens=600,
            )
            lesson["project_step_global"] = resp.choices[0].message.content.strip()
            print(f"  🌍 Global: {lesson['project_step_global'][:80]}...")
        except Exception as e:
            print(f"  ❌ Global ошибка: {e}")
        time.sleep(1)

with open("lessons.json", "w", encoding="utf-8") as f:
    json.dump(lessons, f, ensure_ascii=False, indent=2)

print(f"\nГотово! Шаги проекта сгенерированы для обоих треков.")
