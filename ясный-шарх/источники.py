"""Выгружает шархи из индекса Шамили к себе: данные/источники/<book_id>.jsonl, по странице в строке.
Дальше досье собирается без поиска и без JVM. Повторный запуск пропускает готовые книги.

    python3 ясный-шарх/источники.py
"""
import glob, json, os, sqlite3, subprocess, tempfile

ЗДЕСЬ = os.path.dirname(os.path.abspath(__file__))
ПАПКА = os.path.join(ЗДЕСЬ, '../данные/источники')
ШАМИЛЯ = '/opt/shamela'
ИНДЕКС = f'{ШАМИЛЯ}/database/store/page'
КЛАССЫ = f'{ШАМИЛЯ}/app/lucene/2/*:' + os.path.expanduser('~/projects/tools/shamela/search')
КНИГИ = {1673: 'Фатх аль-Бари', 5756: 'Умдат аль-Кари', 137: 'Фатх Ибн Раджаба', 949: 'Джами аль-улюм', 8176: 'Миркат'}
ЯВА = '/usr/lib/jvm/java-21-openjdk/bin/java'
ЗА_РАЗ = 400


def страницы(книга):
    файл = glob.glob(f'{ШАМИЛЯ}/database/book/*/{книга}.db')[0]
    с = sqlite3.connect(файл)
    return с.execute('select id, part, page, number from page order by id').fetchall()


def разобрать(сырое):
    тело = сырое.split('==========\n', 1)[1]
    основа, _, сноска = тело.partition('--- الهامش ---')
    return основа.strip(), сноска.strip()


def выгрузить(книга):
    путь = f'{ПАПКА}/{книга}.jsonl'
    if os.path.exists(путь):
        return
    стр = страницы(книга)
    with tempfile.TemporaryDirectory() as врем:
        for от in range(0, len(стр), ЗА_РАЗ):  # DumpPages --by-id берёт не больше 400 страниц
            пары = f'{врем}/пары.txt'
            with open(пары, 'w') as ф:
                ф.write(''.join(f'{книга}\t{с[0]}\n' for с in стр[от:от + ЗА_РАЗ]))
            subprocess.run([ЯВА, '-cp', КЛАССЫ, 'DumpPages', ИНДЕКС, пары, f'{врем}/вых', '--by-id'], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        нет = 0
        with open(путь + '.tmp', 'w', encoding='utf-8') as ф:
            for ид, том, лист, номер in стр:
                файл = f'{врем}/вых/{книга}-{ид}.txt'
                if not os.path.exists(файл):
                    нет += 1
                    continue
                основа, сноска = разобрать(open(файл, encoding='utf-8').read())
                ф.write(json.dumps({'id': ид, 'v': том, 'p': лист, 'n': номер, 't': основа, 'f': сноска},
                                   ensure_ascii=False) + '\n')
    os.replace(путь + '.tmp', путь)
    print(КНИГИ[книга], 'страниц', len(стр), 'без текста', нет, flush=True)


os.makedirs(ПАПКА, exist_ok=True)
for к in КНИГИ:
    выгрузить(к)
