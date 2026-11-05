"""Забирает сборник с hadith.dev (جامع خادم الحرمين الشريفين, открыт для разработчиков) к себе:
данные/сырьё/<книга>/_список.json, <main_id>.json на каждую запись-лист и <main_id>.t.json —
другие передачи этого хадиса по всем сборникам. Повторный запуск докачивает недостающее.
Вежливо: четыре потока с паузой, не больше 3 запросов/с.

    python3 скачать.py 1        # Бухари
    python3 скачать.py 1 2      # Бухари, затем Муслим
"""
import json, os, sys, time, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(HERE,'данные/сырьё')
UA={'User-Agent':'isnad-project (tawhiid.com; research, polite crawler)'}
ПАУЗА=0.3; ПОТОКОВ=4

def get(url,tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60) as r: return json.load(r)
        except Exception as e:
            err=e; time.sleep(5*(i+1))
    print('сбой',url,err,file=sys.stderr,flush=True); return None

def скачать(книга):
    папка=os.path.join(RAW,str(книга)); os.makedirs(папка,exist_ok=True)
    файл=os.path.join(папка,'_список.json')
    if os.path.exists(файл): список=json.load(open(файл,encoding='utf-8'))
    else:
        список=get(f'https://hadith.dev/api/books/{книга}/hadiths')
        json.dump(список,open(файл,'w',encoding='utf-8'),ensure_ascii=False)
    листья=[з['main_id'] for з in список if з['is_leaf']]
    def есть(м): return all(os.path.exists(os.path.join(папка,f'{м}{х}.json')) for х in ('','.t'))
    нет=[м for м in листья if not есть(м)]
    print(f'книга {книга}: записей {len(список)}, листьев {len(листья)}, докачать {len(нет)}',flush=True)
    счёт=[0]; замок=threading.Lock()
    def одна(м):
        for хвост,адрес in (('',f'hadith/{м}'),('.t',f'hadith/{м}/takhrij')):
            путь=os.path.join(папка,f'{м}{хвост}.json')
            if os.path.exists(путь): continue
            д=get('https://hadith.dev/api/'+адрес)
            if д is not None:
                врем=путь+'.tmp'
                json.dump(д,open(врем,'w',encoding='utf-8'),ensure_ascii=False); os.replace(врем,путь)
            time.sleep(ПАУЗА)
        with замок:
            счёт[0]+=1
            if счёт[0]%500==0: print(f'книга {книга}: {счёт[0]} из {len(нет)}',flush=True)
    with ThreadPoolExecutor(ПОТОКОВ) as п: list(п.map(одна,нет))
    готово=sum(есть(м) for м in листья)
    print(f'книга {книга} готова: {готово} из {len(листья)}',flush=True)

for к in sys.argv[1:]: скачать(int(к))
