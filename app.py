import re
import json
import urllib.request
import html
import streamlit as st

st.set_page_config(page_title="Пешитта — бесплатный разбор", layout="wide")
st.title("Арамейская Библия · сравнительный анализ")
st.caption("Бесплатный экспериментальный словарный разбор без API. Это не полноценный автоматический перевод.")

# Small manually curated starter lexicon. Expand only with checked attestations.
LEXICON = {
    "ܒܪܫܝܬ": ("в начале", "напачатку", "na początku", "in the beginning", "ܒ + ܪܫܝܬ: предлог «в» + «начало»"),
    "ܐܝܬܘܗܝ": ("был / существовал", "быў / існаваў", "był / istniał", "was / existed", "экзистенциальная конструкция с местоименным элементом; контекст важен"),
    "ܐܝܬܘܗܘ": ("существует (чтение проверить)", "існуе (праверыць чытанне)", "istnieje (sprawdź zapis)", "exists (verify reading)", "форма требует сверки с изданием Пешитты"),
    "ܡܠܬܐ": ("слово", "слова", "słowo", "word", "существительное женского рода, эмфатическое состояние; также «речь»"),
    "ܗܘܐ": ("был / стал", "быў / стаў", "był / stał się", "was / became", "глагол ܗܘܐ; значение зависит от контекста"),
    "ܘ": ("и", "і", "i", "and", "союз, часто присоединяется к следующему слову"),
    "ܐܠܗܐ": ("Бог", "Бог", "Bóg", "God", "существительное, эмфатическое состояние"),
    "ܠܘܬ": ("у / с / к", "у / з / да", "u / z / do", "with / toward", "предлог; значение зависит от конструкции"),
    "ܗܘ": ("он / тот", "ён / той", "on / ten", "he / that", "местоимение"),
    "ܢܘܗܪܐ": ("свет", "святло", "światło", "light", "существительное"),
    "ܚܝܐ": ("жизнь / живые", "жыццё / жывыя", "życie / żywi", "life / living", "неоднозначная форма; нужен контекст"),
}
LANG = {"Русский": 0, "Белорусский": 1, "Польский": 2, "Английский": 3}
tradition = st.selectbox("Источник и языковая традиция", [
    "Сирийская Пешитта (восточноарамейская традиция)",
    "Таргум Онкелоса (еврейский литературный арамейский)",
    "Западноарамейские тексты (источник требуется указать)",
])
st.caption("Важно: Таргум Онкелоса не является дословной записью галилейской речи Иисуса I века.")
@st.cache_data(ttl=86400, show_spinner=False)
def load_onkelos_chapter(chapter):
    url = f"https://www.sefaria.org/api/texts/Onkelos_Genesis.{chapter}?context=0&commentary=0"
    req = urllib.request.Request(url, headers={"User-Agent": "AramaicBibleResearch/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.load(response)
    verses = data.get("he", [])
    if not isinstance(verses, list) or not verses:
        raise ValueError("Текст главы отсутствует в ответе библиотеки")
    return [html.unescape(re.sub(r"<[^>]+>", "", str(v))) for v in verses]

if tradition == "Таргум Онкелоса (еврейский литературный арамейский)":
    chapter = st.selectbox("Книга Бытия — глава", range(1, 51))
    st.caption("Источник: Sefaria, Targum Onkelos on Genesis. Текст загружается по главам из внешней библиотеки, не генерируется нейросетью.")
    try:
        verses = load_onkelos_chapter(chapter)
        verse_number = st.selectbox("Стих", ["Вся глава"] + list(range(1, len(verses) + 1)))
        chosen = verses if verse_number == "Вся глава" else [verses[verse_number - 1]]
        st.text_area("Арамейский текст выбранного фрагмента", value="\\n".join(
            f"{i if verse_number == 'Вся глава' else verse_number}. {v}" for i, v in enumerate(chosen, 1)
        ), height=260)
        st.markdown(f"[Открыть источник в Sefaria](https://www.sefaria.org/Onkelos_Genesis.{chapter})")
    except Exception as exc:
        st.warning("Не удалось загрузить главу из Sefaria. Проверьте подключение или откройте источник по ссылке.")
        st.markdown(f"[Глава {chapter} в Sefaria](https://www.sefaria.org/Onkelos_Genesis.{chapter})")

reference = st.text_input("Место и источник (например, Бытие 1:1, издание/рукопись)")
source = st.text_area("Текст источника (сохраняется без изменения)", value="ܒܪܫܝܬ ܐܝܬܘܗܝ ܡܠܬܐ", height=140)
language = st.selectbox("Язык", list(LANG))
mode = st.selectbox("Режим", ["Буквальный", "Литературный", "Филологический анализ"])
st.info("Бесплатная версия знает ограниченный набор слов. Неизвестные формы сохраняются без выдуманного перевода. Литературный режим пока показывает только черновой подстрочник.")
if st.button("Подготовить перевод", type="primary"):
    if tradition != "Сирийская Пешитта (восточноарамейская традиция)":
        st.warning("Для этой традиции словарь пока не подключён. Текст сохранён для просмотра; перевод не создаётся без проверенной лексической базы.")
        st.code(source)
        st.stop()
    words = re.findall(r"[\u0700-\u074F\u0860-\u086F]+|[^\s]+", source)
    if not source.strip():
        st.warning("Введите сирийский текст.")
    elif not words:
        st.warning("Не обнаружен текст.")
    else:
        rows, glosses, unknown = [], [], []
        for word in words:
            clean = re.sub(r"[\u0730-\u074A\u064B-\u065F]", "", word)
            item = LEXICON.get(clean)
            if item:
                gloss = item[LANG[language]]
                rows.append({"Оригинал": word, "Значение": gloss, "Примечание": item[4]})
                glosses.append(gloss)
            else:
                rows.append({"Оригинал": word, "Значение": "—", "Примечание": "Нет в проверенном словаре"})
                glosses.append(f"[{word}]")
                unknown.append(word)
        st.subheader("Источник")
        st.write(tradition)
        st.write(reference or "Рукопись/издание не указаны; атрибуция не подтверждена.")
        st.code(source)
        st.subheader("Буквальный подстрочник (не литературный перевод)")
        st.write(" · ".join(glosses))
        if mode == "Литературный":
            st.warning("Связный литературный перевод пока недоступен без отдельного переводческого движка.")
        st.subheader("Филологические примечания и пословный разбор")
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if unknown:
            st.warning("Не распознаны: " + ", ".join(unknown) + ". Не используйте подстрочник как готовый перевод.")
        st.caption("Для научного использования сверяйте написание, огласовку, морфологию и контекст с критическим изданием Пешитты.")
