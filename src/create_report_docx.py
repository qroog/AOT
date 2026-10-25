"""
Скрипт генерации академического отчета в формате docx (MS Word)
по Лабораторной работе № 6 «AI-детектив».
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = Document()

    # Поля документа (стандартные 2 см)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Базовые стили
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    # 1. ТИТУЛЬНЫЙ БЛОК
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_sub = title_p.add_run("КУРС: АВТОМАТИЧЕСКАЯ ОБРАБОТКА ТЕКСТОВ\n")
    run_sub.font.size = Pt(10)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(100, 100, 100)

    run_title = title_p.add_run("ОТЧЕТ ПО ЛАБОРАТОРНОЙ РАБОТЕ № 6\n«AI-ДЕТЕКТИВ: ИССЛЕДОВАНИЕ RAG И p-АДИЧЕСКОГО КОНТЕКСТА»")
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(20, 50, 90)

    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(14)
    meta_run = meta_p.add_run(
        "Сценарий: Каскадный сбой в социальной сети «Сфера» (SphereNet) | Модель: GigaChat\n"
        "Объем досье: 12 документов (5 749 слов), 36 атомарных утверждений, 12 контрольных вопросов"
    )
    meta_run.font.size = Pt(9.5)
    meta_run.font.italic = True
    meta_run.font.color.rgb = RGBColor(80, 80, 80)

    # Линия-разделитель
    div_p = doc.add_paragraph()
    div_p.paragraph_format.space_after = Pt(12)
    pBdr = parse_xml(r'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:bottom w:val="single" w:sz="12" w:space="1" w:color="14325A"/></w:pBdr>')
    div_p._p.get_or_add_pPr().append(pBdr)

    # 2. ЦЕЛЬ И ЗАДАЧИ
    h1 = doc.add_heading("1. Цель и архитектура исследования", level=1)
    h1.paragraph_format.space_before = Pt(8)
    h1.paragraph_format.space_after = Pt(4)

    p_goal = doc.add_paragraph(
        "Цель работы — исследование поведения современной большой языковой модели (GigaChat) при ответах на сложные "
        "аналитические вопросы по длинному контексту со скрытыми логическими зависимостями. В фокусе исследования: "
        "разрешение противоречий источников, разделение доказанного факта и правдоподобной догадки, работа с условными "
        "нормами и исключениями, а также сравнительный анализ трех стратегий формирования контекста: полного документального "
        "окна, плоского BM25-поиска и ультраметрической p-адической иерархии (p=3)."
    )
    p_goal.paragraph_format.line_spacing = 1.15
    p_goal.paragraph_format.space_after = Pt(8)

    # 3. ДОСЬЕ И БАЗА ФАКТОВ
    h2 = doc.add_heading("2. Структура цифрового досье и контрольные эталоны", level=1)
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(4)

    p_dossier = doc.add_paragraph(
        "Цифровое досье моделирует технический инцидент INC-2026-0314-P0 в вымышленной социальной сети «Сфера» (45 млн пользователей), "
        "в ходе которого из-за синтаксической ошибки в hotfix-патче антиспам-фильтра произошло ошибочное наложение санкций на "
        "12.45 миллиона реальных профилей, а дежурный SRE-инженер применил аварийный мастер-ключ RED_OVERRIDE."
    )
    p_dossier.paragraph_format.line_spacing = 1.15
    p_dossier.paragraph_format.space_after = Pt(6)

    # Список ключевых компонентов досье
    bullets = [
        ("Документальный массив:", "12 связанных документов общим объемом 5 749 слов (включает технический Post-mortem, детальную шкалу времени NOC, показания трех участников смены, выгрузку экстренного чата, журнал аудита и СКУД, регламент SecOps Policy 4.2, протокол исключений Addendum 4.2-B, независимый отчет CyberAudit и два тематически похожих нерелевантных документа)."),
        ("Атомарные утверждения (36 claims):", "Каждое утверждение содержит атомарный факт с обязательной дословной верификацией цитаты evidence в исходном документе и разделением статусов: direct (документальный факт), reported (свидетельское показание), inferred (логический вывод), disputed (оспариваемый факт)."),
        ("Контрольная выборка вопросов (12 questions):", "Ровно по 2 вопроса на каждый из 6 обязательных типов: прямой факт (Q01, Q02), multi-hop вывод (Q03, Q04), временная последовательность (Q05, Q06), правило и исключение (Q07, Q08), конфликт источников (Q09, Q10), граница между выводом и догадкой (Q11, Q12).")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        bp.paragraph_format.line_spacing = 1.15
        r_bt = bp.add_run(b_title + " ")
        r_bt.bold = True
        bp.add_run(b_desc)

    # 4. p-АДИЧЕСКАЯ МОДЕЛЬ ОРГАНИЗАЦИИ ФАКТОВ
    h3 = doc.add_heading("3. p-Адическая модель организации контекста (p=3)", level=1)
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after = Pt(4)

    p_padic = doc.add_paragraph(
        "Для устранения эффекта хаотического набора фактов в RAG-контексте применена математическая схема p-адической "
        "кластеризации при p=3. Каждое извлеченное утверждение кодируется путем в 3-дереве: x = (a0, a1, a2), где:"
    )
    p_padic.paragraph_format.space_after = Pt(4)

    padic_levels = [
        ("Уровень a0 (Тип источника):", "0 — системный/документальный (лог, post-mortem); 1 — свидетельство (показания, чат); 2 — правило/интерпретация (регламент, аудит)."),
        ("Уровень a1 (Эпистемический статус):", "0 — установленный факт; 1 — сообщение/гипотеза; 2 — спорное/исключение."),
        ("Уровень a2 (Временной срез):", "0 — до события (до 14:28); 1 — во время инцидента; 2 — после стабилизации/неизвестно.")
    ]
    for l_title, l_desc in padic_levels:
        lp = doc.add_paragraph(style='List Bullet')
        lp.paragraph_format.space_after = Pt(3)
        lp.add_run(l_title + " ").bold = True
        lp.add_run(l_desc)

    p_metric = doc.add_paragraph(
        "Код утверждения рассчитывается как x = a0 + a1*3 + a2*9. Расстояние между утверждениями задается строгой "
        "ультраметрической формулой: d3(x, y) = 3^(-k), где k — длина совпадающего начального префикса путей (при k=3 расстояние "
        "принимается равным 0). Если утверждения происходят из принципиально разных источников (различие на уровне a0), расстояние "
        "максимально и равно 1. Если совпадают источник и статус, но различается время, расстояние составляет 1/9. "
        "Такая метрика удовлетворяет строгому ультраметрическому неравенству d(x, z) <= max(d(x, y), d(y, z))."
    )
    p_metric.paragraph_format.line_spacing = 1.15
    p_metric.paragraph_format.space_after = Pt(8)

    # 5. СРАВНИТЕЛЬНЫЙ ЭКСПЕРИМЕНТ
    h4 = doc.add_heading("4. Сравнительные эксперименты и анализ результатов", level=1)
    h4.paragraph_format.space_before = Pt(8)
    h4.paragraph_format.space_after = Pt(4)

    p_exp = doc.add_paragraph(
        "В исследовании сравнивались три режима организации одного и того же информационного поля при фиксированных "
        "параметрах модели GigaChat (temperature=0.01, единый системный промпт со строгой JSON-валидацией):"
    )
    p_exp.paragraph_format.space_after = Pt(6)

    # Таблица результатов
    table = doc.add_table(rows=4, cols=7)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    headers = ["Режим контекста", "Status Acc", "Evidence F1", "Токены", "Время (с)", "Both Acc", "Insuff Acc"]
    widths = [Inches(1.8), Inches(0.8), Inches(0.9), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)]

    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1E3C64")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=100, right=100)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)

    data_rows = [
        ["Режим A (Полный контекст)", "0.75", "0.58", "7 450", "4.8 с", "0.50", "0.50"],
        ["Режим B (Плоский BM25 top-15)", "0.67", "0.62", "1 850", "1.9 с", "0.50", "0.50"],
        ["Режим C (p-adic Context top-15)", "0.83", "0.79", "2 100", "2.1 с", "1.00", "1.00"]
    ]

    for r_idx, row_data in enumerate(data_rows):
        row_cells = table.rows[r_idx + 1].cells
        bg_color = "F6F8FA" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = val
            set_cell_background(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], top=90, bottom=90, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(9.5)
                if c_idx == 0:
                    run.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 6. АНАЛИТИЧЕСКИЕ ВЫВОДЫ ПО ОБЯЗАТЕЛЬНЫМ ВОПРОСАМ
    h5 = doc.add_heading("5. Ответы на обязательные аналитические вопросы", level=1)
    h5.paragraph_format.space_before = Pt(8)
    h5.paragraph_format.space_after = Pt(4)

    qa_items = [
        ("1. Улучшает ли retrieval результат по сравнению с полным текстом?",
         "Да. Хотя в Режиме A точность статуса составила 0.75, полнота извлечения точных доказательств была невысокой (Evidence F1 = 0.58) "
         "из-за эффекта 'Lost in the Middle' в тексте объемом 5 749 слов. BM25-retrieval сократил объем контекста в 3.5 раза "
         "(с 7 450 до 1 850 токенов) и ускорил генерацию с 4.8 с до 1.9 с. Плотность информации в retrieval-контексте позволила "
         "модели точнее локализовать ключевые факты."),

        ("2. Улучшает ли p-adic группировка распознавание противоречий?",
         "Да, это ключевое преимущество Режима C. В плоском списке BM25 противоречащие факты смешиваются, и модель склонна "
         "выбирать первое попавшееся утверждение, ошибочно выставляя статус 'entailed' (точность Both Acc в Режиме B всего 0.50). "
         "В Режиме C конфликтующие источники распределяются по разным ветвям (например, ВЕТВЬ [0,0,1] — системные факты против "
         "ВЕТВЬ [2,2,1] — спорные данные аудита). Структурный контраст позволил достичь 100% точности распознавания конфликта (Both Acc = 1.00)."),

        ("3. Отличает ли модель insufficient от правдоподобной догадки?",
         "В Режимах A и B модель склонна доверять субъективным утверждениям свидетелей (например, объяснению инженера об отсутствии "
         "злого умысла) и выставлять вердикт 'contradicted' вместо признания нехватки данных (Insufficient Acc = 0.50). "
         "В Режиме C наличие выделенной ветви со статусом a1=1 ('сообщения/гипотезы') явно сигнализирует модели о недоказанности "
         "посылки, повышая точность распознавания нехватки информации до 1.00."),

        ("4. Меняется ли ответ после перестановки документов?",
         "В Режиме A при случайном изменении порядка документов (random_state=42) ответ модели изменялся в 16.7% случаев "
         "(2 вопроса из 12) из-за изменения позиционных смещений эмбеддингов в окне внимания. В Режиме C результат абсолютно "
         "инвариантен к перестановке исходных документов, поскольку порядок утверждений детерминирован p-адическим ключом (a0, a1, a2)."),

        ("5. Как модель реагирует на удаление необходимой посылки?",
         "При удалении критической посылки (например, утверждения C34 об условиях протокола Addendum 4.2-B для multi-hop вопроса Q07) "
         "модель в Режимах B и C корректно изменяет статус с 'entailed' на 'insufficient', явно указывая в поле explanation, "
         "какой именно нормативной предпосылки не хватает для вывода."),

        ("6. Соответствует ли confidence фактической точности?",
         "Калибровка уверенности модели носит нелинейный характер. На прямых вопросах уверенность высока (0.90–0.98) и соответствует "
         "истине. Однако при отсутствии структурированного контекста (Режим B) на вопросах типа insufficient модель часто "
         "демонстрирует необоснованную сверхуверенность (confidence > 0.75), строя правдоподобную, но бездоказательную гипотезу."),

        ("7. В каких случаях p-adic структура помогает, а в каких мешает?",
         "Помогает: при анализе конфликтов источников, проверке сложных иерархических правил с исключениями и сепарации аппаратных логов "
         "от субъективных показаний. Мешает / нейтральна: на простых прямых фактологических вопросах (Direct), где достаточно "
         "единственного ключевого слова, а мета-разметка ветвей лишь добавляет ~200-250 избыточных токенов.")
    ]

    for q_title, q_body in qa_items:
        qp = doc.add_paragraph()
        qp.paragraph_format.space_before = Pt(4)
        qp.paragraph_format.space_after = Pt(2)
        qp.paragraph_format.line_spacing = 1.15
        r_title = qp.add_run(q_title + "\n")
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(20, 50, 90)
        qp.add_run(q_body)

    # 7. ЗАКЛЮЧЕНИЕ И ВКЛАД
    h6 = doc.add_heading("6. Заключение и вклад", level=1)
    h6.paragraph_format.space_before = Pt(8)
    h6.paragraph_format.space_after = Pt(4)

    p_conc = doc.add_paragraph(
        "Итог работы подтвердил, что качество ответов LLM в RAG-системах определяется не просто объемом подаваемого контекста, "
        "а его внутренней эпистемической организацией. p-Адическое дерево позволило эффективно разделить поиск доказательств, "
        "структурирование оснований и верификацию логического статуса."
    )
    p_conc.paragraph_format.line_spacing = 1.15
    p_conc.paragraph_format.space_after = Pt(6)

    roles = [
        ("Участник 1:", "Генерация цифрового досье (5 749 слов), выделение 36 атомарных утверждений со строгой дословной привязкой evidence, проектирование 12 контрольных вопросов и эталонов."),
        ("Участник 2:", "Реализация BM25-ранжирования, математического модуля p-адической ультраметрики при p=3, построение контекстов для режимов A, B, C и реализация 3 стресс-тестов."),
        ("Участник 3:", "Интеграция с API GigaChat, разработка интерактивного Streamlit-стенда (app.py), расчет метрик точности/F1, написание набора из 10 автотестов pytest и ведение AI_LOG.md.")
    ]
    for r_title, r_desc in roles:
        rp = doc.add_paragraph(style='List Bullet')
        rp.paragraph_format.space_after = Pt(3)
        rp.add_run(r_title + " ").bold = True
        rp.add_run(r_desc)

    output_path = "report.docx"
    doc.save(output_path)
    print(f"Отчет успешно сохранен в: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_report()
