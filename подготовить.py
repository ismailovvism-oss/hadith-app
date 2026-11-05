"""Рабочий файл для переводчика: арабский текст одной книги сборника без разметки.

    python3 подготовить.py 1 2        # книга 2 сборника 1 → данные/рабочее/1-02.md
"""
import json, os, re, sys
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(HERE,'данные/сырьё')

def книги(сборник):
    "Книги сборника по порядку: main_id идёт по порядку издания, left_value нет."
    с=json.load(open(os.path.join(RAW,str(сборник),'_список.json'),encoding='utf-8'))
    по_левому=sorted(с,key=lambda з:з['left_value']); стек=[]; верх=[]
    for з in по_левому:
        while стек and стек[-1]['right_value']<з['left_value']: стек.pop()
        if len(стек)==1: верх.append(з)
        if not з['is_leaf']: стек.append(з)
    верх.sort(key=lambda з:з['main_id'])
    с.sort(key=lambda з:з['main_id'])
    return верх,с

def чисто(т):
    т=re.sub(r'<[^>]+>','',т).replace('&quot;','"')
    return re.sub(r'\s+',' ',т).strip()

def разобрать(т):
    "(вступление, иснад, текст): вступление до <حديث, иснад до первого <متن, дальше текст."
    исходный=т
    т=re.sub(r'<رقم_الفقرة[^>]*/>|<الصفحات[^>]*/>|<نه/>','',т)
    т=re.sub(r'<رقم_حديث[^>]*>.*?</رقم_حديث>','',т,flags=re.S)
    т=re.sub(r'<(سند_مخفي|متن_مخفي)[^>]*>.*?</\1>|<[^<>]*\sنص="[^"]*"[^<>]*/>','',т,flags=re.S)
    if '<حديث' not in т:
        есть_номер='<رقم_حديث' in исходный
        return ('','',чисто(т)) if есть_номер else (чисто(т).strip(' -'),'','')
    вст,ост=т.split('<حديث',1); ост='<حديث'+ост
    м=re.search(r'<متن(?=[\s>])',ост)
    if м:
        иснад,текст=ост[:м.start()],ост[м.start():]
    else: иснад,текст=ост,''
    return чисто(вст),чисто(иснад).lstrip('- ').strip(),чисто(текст)

if __name__=='__main__':
    сб,н=int(sys.argv[1]),int(sys.argv[2])
    верх,с=книги(сб); кн=верх[н-1]; след=верх[н]['main_id'] if н<len(верх) else 10**9
    вых=[f'# {кн["tarf"]}\n']; слов=0
    for з in с:
        if not кн['main_id']<з['main_id']<след: continue
        if not з['is_leaf']: вых.append(f'\n## {з["tarf"]}\n'); continue
        д=json.load(open(os.path.join(RAW,str(сб),f'{з["main_id"]}.json'),encoding='utf-8'))
        вст,иснад,текст=разобрать(д['hadith']['content']); слов+=len(текст.split())
        if вст: вых.append(f'ВСТУПЛЕНИЕ: {вст}\n')
        if иснад or текст:
            вых.append(f'### {з["tarqeem_matboa1"]}\nИСНАД: {иснад}\nТЕКСТ: {текст}\n')
    os.makedirs(os.path.join(HERE,'данные/рабочее'),exist_ok=True)
    п=os.path.join(HERE,f'данные/рабочее/{сб}-{н:02}.md')
    open(п,'w',encoding='utf-8').write('\n'.join(вых))
    print(п,'слов текста',слов)
