import json
import urllib.request
import urllib.error
import streamlit as st

st.set_page_config(page_title="Пешитта — переводчик", layout="wide")
st.title("ܦܫܝܛܬܐ · Переводчик арамейской Библии")
st.caption("Экспериментальный перевод сирийского арамейского. Результаты требуют филологической проверки.")
source = st.text_area("Арамейский оригинал", height=180, placeholder="Вставьте сирийский текст")
language = st.selectbox("Язык перевода", ["Русский", "Белорусский", "Польский", "Английский"])
mode = st.selectbox("Режим", ["Буквальный", "Литературный", "Филологический анализ"])
try:
    key = st.secrets.get("OPENAI_API_KEY", "")
except Exception:
    key = ""
if not key:
    st.info("Для автоматического перевода настройте OPENAI_API_KEY в Streamlit → App settings → Secrets. Никогда не добавляйте ключ в публичный GitHub.")
if st.button("Перевести", type="primary"):
    if not source.strip():
        st.warning("Введите текст.")
    elif not key:
        st.error("Автоматический перевод пока недоступен: не настроен API-ключ.")
    else:
        instructions = (
            "Переводи предоставленный сирийский арамейский текст непосредственно на целевой язык, "
            "не подменяя оригинал известными библейскими переводами. "
            "Не выдумывай этимологии и источники. Указывай сомнительные чтения и неопределённость. "
            f"Язык результата: {language}. Режим: {mode}. "
            "Буквальный: сохраняй синтаксис и помечай добавленные слова. "
            "Литературный: сохраняй смысл и читаемость. "
            "Филологический анализ: объясняй лексику, морфологию и альтернативные значения."
        )
        payload = json.dumps({
            "model": "gpt-4.1-mini",
            "instructions": instructions,
            "input": source.strip(),
            "max_output_tokens": 1800
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST"
        )
        with st.spinner("Переводим..."):
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    result = json.load(response)
                translated = "\n".join(
                    part.get("text", "")
                    for item in result.get("output", [])
                    for part in item.get("content", [])
                    if part.get("type") == "output_text"
                ).strip()
                if translated:
                    st.subheader("Результат")
                    st.write(translated)
                    st.caption("Машинный перевод; сверяйте с текстом Пешитты.")
                else:
                    st.error("Сервис не вернул перевод.")
            except urllib.error.HTTPError as exc:
                st.error(f"Ошибка API (HTTP {exc.code}). Проверьте ключ, баланс и доступ к модели.")
            except Exception:
                st.error("Ошибка соединения с сервисом перевода.")
