#!/usr/bin/env python3
"""Собирает пилот: пилот-1.md (текст) + данные/*.json (арабский, иснады, передатчики) → пилот-1.html."""
import html, json, os, re

ЗДЕСЬ = os.path.dirname(os.path.abspath(__file__))
ПЕРЕДАТЧИКИ = json.load(open(f'{ЗДЕСЬ}/данные/передатчики.json', encoding='utf-8'))

МЕТА = {
    'bukhari-30': ('b30', 'Сахих аль-Бухари · Книга веры · 30'),
    'bukhari-13': ('b13', 'Сахих аль-Бухари · Книга веры · 13'),
    'bukhari-34': ('b34', 'Сахих аль-Бухари · Книга веры · 34'),
    'tirmidhi-2317': ('t2317', 'Джами ат-Тирмизи · 2317 · вне аль-Бухари'),
}
ЦЕПИ = {
    'bukhari-30': [[5495, 2587, 2779, 6766, 6261, 1181]],
    'bukhari-13': [[5495, 6085, 6931, 2779, 5183, 822], [5495, 6085, 6931, 1470, 5183, 822]],
    'bukhari-34': [[5495, 5178, 2472, 2638, 3909, 6088, 3823]],
    'tirmidhi-2317': [['ат-Тирмизи', 502, 3163, 674, 3375, 5203, 5917, 3745, 3320]],
}


def инлайн(т):
    т = html.escape(т, quote=False)
    т = re.sub(r'==(.+?)==', r'<mark>\1</mark>', т)
    т = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', т)
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', т)


def арабский(ключ):
    """Размеченный текст hadith.dev → глава, иснад, матн, хвост; передатчики становятся ссылками."""
    т = json.load(open(f'{ЗДЕСЬ}/данные/{ключ}.json', encoding='utf-8'))['hadith']['content']
    т = re.sub(r'<رقم_الفقرة[^>]*/>|<الصفحات[^>]*/>|<نه/>', '', т)
    т = re.sub(r'<رقم_حديث[^>]*>.*?</رقم_حديث>', '', т, flags=re.S)

    def рави(м):
        нид, текст = м.group(1), м.group(2).strip()
        хвост = ''
        if текст.endswith('،'):
            текст, хвост = текст[:-1].rstrip(), ' ،'
        if нид in ПЕРЕДАТЧИКИ:
            return f'<a class="r" data-id="{нид}">{текст}</a>{хвост} '
        return текст + хвост + ' '

    т = re.sub(r'<راوي[^>]*?ربط="(\d+)"[^>]*>(.*?)</راوي>', рави, т, flags=re.S)
    т = т.replace('<متن', '\x01<متن').replace('</متن>', '\x02')
    т = re.sub(r'<حديث[^>]*>', '\x03', т)
    т = re.sub(r'</?(?!a\b|/a\b)[^\x00-\x7f][^>]*>', '', т)
    глава, _, тело = т.partition('\x03')
    иснад, _, ост = тело.partition('\x01')
    матн, _, хвост = ост.partition('\x02')
    чисто = lambda с: re.sub(r'\s+', ' ', с.replace('\x03', '')).strip(' -.')
    return чисто(глава), чисто(иснад), чисто(матн), чисто(хвост)


def цепи(ключ):
    строки = []
    for н, цепь in enumerate(ЦЕПИ[ключ]):
        части = []
        for зв in цепь:
            if isinstance(зв, str):
                части.append(f'<span class="ch ch-n">{зв}</span>')
            else:
                п = ПЕРЕДАТЧИКИ[str(зв)]
                части.append(f'<a class="ch l{п["level"]}" data-id="{зв}">{п["ru"]}</a>')
        части.append('<span class="ch ch-p">Пророк ﷺ</span>')
        метка = 'Вторая цепь' if н else 'Иснад'
        строки.append(f'<div class="chain"><span class="lbl">{метка}</span>' + '<i>от</i>'.join(части) + '</div>')
    return ''.join(строки)


def статья(блок):
    шапка, *строки = блок.strip().split('\n')
    ключ, заглавие = [с.strip() for с in шапка[3:].split('|')]
    якорь, адрес = МЕТА[ключ]
    глава, иснад, матн, хвост = арабский(ключ)
    перевод = где = оценка = ''
    тело, диалог, список = [], [], None
    передатчик = ''
    рассказы = 0

    def сброс():
        nonlocal диалог
        if диалог:
            тело.append('<p class="dlg">' + '<br>'.join(диалог) + '</p>')
            диалог = []

    for стр in строки:
        с = стр.strip()
        if not с:
            сброс()
            continue
        if с.startswith('Перевод: '):
            перевод = инлайн(с[9:])
        elif с.startswith('Где: '):
            где = инлайн(с[5:])
        elif с.startswith('Оценка: '):
            оценка = инлайн(с[8:])
        elif с.startswith('Передатчик: '):
            передатчик = инлайн(с[12:])
        elif с == 'Что взять:':
            сброс()
            список = []
        elif с.startswith('- ') and список is not None:
            список.append(инлайн(с[2:]))
        elif с.startswith('— '):
            диалог.append(инлайн(с))
        elif с.startswith('Рассказ: '):
            сброс()
            текст, пометка = с[9:].split(' | ')
            рассказы += 1
            тело.append(f'<aside class="story"><p>{инлайн(текст)}</p><p class="flag">{инлайн(пометка)}</p></aside>')
        else:
            сброс()
            тело.append(f'<p>{инлайн(с)}</p>')
    сброс()
    вывод = ''.join(f'<li>{п}</li>' for п in (список or []))
    return (якорь, заглавие, f'''
<article id="{якорь}">
  <p class="eyebrow">{адрес}</p>
  <h2>{инлайн(заглавие)}</h2>
  <section class="ar" lang="ar" dir="rtl">
    {f'<p class="bab">{глава}</p>' if глава else ''}
    <p class="isnad">{иснад}</p>
    <p class="matn">{матн}</p>
    {f'<p class="isnad">{хвост}</p>' if хвост else ''}
  </section>
  {цепи(ключ)}
  <p class="tr">{перевод}</p>
  <p class="where">{где}</p>
  {f'<p class="where">{оценка}</p>' if оценка else ''}
  <div class="body">{''.join(тело)}</div>
  <section class="take"><h3>Что взять</h3><ul>{вывод}</ul></section>
  {f'<p class="narr"><strong>Передатчик.</strong> {передатчик}</p>' if передатчик else ''}
</article>''')


исходник = open(f'{ЗДЕСЬ}/пилот-1.md', encoding='utf-8').read()
блоки = [б for б in re.split(r'\n---\n', исходник) if б.strip().startswith('## ')]
статьи = [статья(б) for б in блоки]
оглавление = ''.join(f'<a class="toc" href="#{я}" data-go="{я}">{инлайн(з)}</a>' for я, з, _ in статьи)
шаблон = open(f'{ЗДЕСЬ}/шаблон.html', encoding='utf-8').read()
готово = (шаблон.replace('{{ОГЛАВЛЕНИЕ}}', оглавление)
          .replace('{{СТАТЬИ}}', ''.join(т for _, _, т in статьи))
          .replace('{{ПЕРЕДАТЧИКИ}}', json.dumps(ПЕРЕДАТЧИКИ, ensure_ascii=False).replace('</', '<\\/')))
open(f'{ЗДЕСЬ}/пилот-1.html', 'w', encoding='utf-8').write(готово)
print('собрано', len(готово) // 1024, 'КБ')
