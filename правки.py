#!/usr/bin/env python3
"""Правки из режима редактора: лежат в воркере синхронизации под кодом из данные/код-редактора.txt.
Адреса: bukhari/11/876/ru/0 — абзац перевода, sharh/bukhari-886/3 — замечание к абзацу шарха, q/<id> — ответ на вопрос
(data/questions.json; в записи «old» стоят место и текст вопроса).

    python3 правки.py                        # показать открытые
    python3 правки.py применить [--проба]    # внести текстовые правки в перевод/, замечания остаются открытыми
    python3 правки.py ответ <адрес> "текст"  # ответить на замечание и закрыть его

После «применить» запустить собрать.py.
"""
import datetime, json, os, re, sys, urllib.request

ЗДЕСЬ = os.path.dirname(os.path.abspath(__file__))
СИНК = 'https://tafsir-sync.qaadiy-tafsir.workers.dev/v1/'
КОД = os.environ.get('HADITH_EDIT_CODE') or open(f'{ЗДЕСЬ}/данные/код-редактора.txt').read().strip()
UA = {'User-Agent': 'Mozilla/5.0 hadith-app', 'Content-Type': 'application/json'}
ПАПКИ = {'bukhari': 'бухари'}


def загрузить():
    return json.load(urllib.request.urlopen(urllib.request.Request(СИНК + КОД, headers=UA), timeout=30)).get('edits', {})


def сохранить(правки):
    тело = json.dumps({'edits': правки}, ensure_ascii=False).encode()
    urllib.request.urlopen(urllib.request.Request(СИНК + КОД, data=тело, headers=UA, method='PUT'), timeout=30)


def сейчас():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def открытые(правки):
    return {а: п for а, п in sorted(правки.items()) if not п.get('del') and п.get('st') != 'ok'}


def внести(адрес, старое, новое, строки):
    "Меняет строки файла книги на месте; возвращает текст ошибки или None."
    ч = адрес.split('/')
    if ч[2] == 'ch':
        главы = [i for i, с in enumerate(строки) if с.startswith('## ') and not с.startswith('## Вопросы')]
        начало = главы[int(ч[3])]
        if ч[4] == 't':
            строки[начало] = f'## Глава: {новое}' if новое else '## Глава'
            return None
        конец = next((i for i in range(начало + 1, len(строки)) if строки[i].startswith(('### ', '## '))), len(строки))
    else:
        начало = next((i for i, с in enumerate(строки) if re.match(rf'### {re.escape(ч[2])}\s*\|', с)), None)
        if начало is None:
            return 'хадис не найден'
        if ч[3] == 't':
            строки[начало] = f'### {ч[2]} | {новое}'
            return None
        конец = next((i for i in range(начало + 1, len(строки)) if строки[i].startswith(('### ', '## '))), len(строки))
    for i in range(начало, конец):
        if строки[i].strip() == старое.strip():
            строки[i] = новое
            return None
    return 'старый текст не найден, файл уже менялся'


def показать(правки):
    откр = открытые(правки)
    print('открытых правок:', len(откр))
    for а, п in откр.items():
        print(f'\n{а}')
        if п.get('new') is not None:
            print('  было:  ', п.get('old', '')[:300])
            print('  стало: ', п['new'][:300])
        elif п.get('old'):
            print('  вопрос: ' if а.startswith('q/') else '  текст: ', п['old'][:400 if а.startswith('q/') else 200])
        if п.get('note'):
            print('  ответ:    ' if а.startswith('q/') else '  замечание:', п['note'])


def применить(правки, проба):
    книги, ошибки, внесено = {}, [], 0
    for а, п in открытые(правки).items():
        if п.get('new') is None or а.startswith(('sharh/', 'q/')):
            continue
        ч = а.split('/')
        файл = f'{ЗДЕСЬ}/перевод/{ПАПКИ[ч[0]]}/{int(ч[1]):02}.md'
        строки = книги.setdefault(файл, open(файл, encoding='utf-8').read().split('\n'))
        ош = внести(а, п.get('old', ''), п['new'], строки)
        if ош:
            ошибки.append(f'{а}: {ош}')
            continue
        внесено += 1
        п['at'] = сейчас()
        if п.get('note'):
            п['new'], п['reply'] = None, 'Текст внесён, замечание читаю'
        else:
            п['st'], п['reply'] = 'ok', 'Внесено'
    print('внесено', внесено, 'ошибок', len(ошибки), *ошибки, sep='\n')
    if проба:
        return
    for файл, строки in книги.items():
        open(файл, 'w', encoding='utf-8').write('\n'.join(строки))
    if внесено:
        сохранить(правки)


правки = загрузить()
if len(sys.argv) > 1 and sys.argv[1] == 'применить':
    применить(правки, '--проба' in sys.argv)
elif len(sys.argv) > 3 and sys.argv[1] == 'ответ':
    п = правки[sys.argv[2]]
    п.update(st='ok', reply=sys.argv[3], at=сейчас())
    сохранить(правки)
else:
    показать(правки)
