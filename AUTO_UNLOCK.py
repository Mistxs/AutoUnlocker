import requests
from flask import Flask
from flask import request, render_template
import logging
import datetime
import time

from config import headers, u_headers

app = Flask(__name__)


@app.route('/')
def home():
    logs = {'date': '2023-02-25 20:43:05.148361', 'type': 'newhook', 'salon': '547114', 'url': 'http://hgggas.ru'}
    return render_template('page.html', logs=logs["date"])


@app.route('/logs')
def logs():
    logs = {'date': '2023-02-25 20:43:05.148361', 'type': 'newhook', 'salon': '547114', 'url': 'http://hgggas.ru'}
    return render_template('logs.html', logs=logs["date"])


@app.route('/getrec', methods=['POST'])
def process_json():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        request_data = request.json
        if request_data["resource"] == "record" and request_data["status"] == "create":
            check_hook(request_data)

        return '200'
    else:
        return 'Content-Type not supported!'


def check_hook(data):
    if data["data"]["online"] == True:

        pretty_date = datechanger(data["data"]["create_date"])
        salon_id = data["data"]["company_id"]
        document = data["data"]["documents"][0]["id"]
        rec_id = data["data"]["id"]
        checkdb(salon_id)
        now = datetime.datetime.now()
        pretty_output_first(salon_id, rec_id, now)
        time.sleep(660)
        recheck(salon_id, pretty_date, document, rec_id, now)

    else:
        print("Не онлайн запись")


ids = []


def checkdb(id):
    print('запустили checkdb, содержимое массива: ', ids)
    if id not in ids:
        ids.append(id)
        f = open('salon_db.txt', 'a')
        f.write("\n")
        p_out = f'''
        <p style="font-size:14px; color: #49456a"> Прямая ссылка на настройку хуков
        <a href = "https://yclients.com/settings/web_hook/{id}/"> https://yclients.com/settings/web_hook/{id}/ </a></p>
'''
        f.write(p_out)
        f.close()
    print(ids)


def pretty_output_first(salon_id, rec_id, timestamp):
    pretty_output = f'''
    <p style= "color: #384258; font-size: 14px; margin-left:10px">
    {timestamp}</br>Получен хук</br>Ссылка на запись <a href = "https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}"> 
    https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}</a></br> Ожидаем запуска речека (10м) Филиал {salon_id}.</p>

    '''
    print(pretty_output)
    f = open('log.txt', 'a')
    f.write(pretty_output)
    f.close()


def pretty_output_second(code, res, doc, kkm, salon_id, rec_id, timestamp):
    colorscheme = "border: 1px solid; padding: 10px; font-size: 14px; width: 80%"
    pretty_output = "none"
    if code == 1:
        pretty_output = f'''
    <p style = "color:#076e1b; {colorscheme}">
    {timestamp}</br>Ссылка на запись <a href = "https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}"> 
    https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}</a></br>
    Речек записи выполнен. Необходима разблокировка.</br>
    Ответ от тестера: {res}</p>'''
    elif code == 2:
        pretty_output = f'''
    <p style = "color:#f31717; {colorscheme}">
    {timestamp}</br>Ссылка на запись <a href = "https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}"> 
    https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}</a></br>
    Речек записи выполнен. Требуется ручная разблокировка!</br>
    UPDATE documents SET bill_print_status = 1 WHERE id = {doc};</br>
    UPDATE kkm_transactions SET status = 3 WHERE id in {kkm};</p>'''
    elif code == 3:
        pretty_output = f'''
    <p style = "color:#2716a9; {colorscheme}">
    {timestamp}</br>Ссылка на запись <a href = "https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}"> 
    https://yclients.com/timetable/{salon_id}#main_date=2023-01-28&open_modal_by_record_id={rec_id}</a></br>
    Речек записи выполнен. Анлок не требуется.</br>
    Причина: isblock = {doc} and isprint = {kkm}</p>'''
    print(pretty_output)
    f = open('log.txt', 'a')
    f.write("\n")
    f.write(pretty_output)
    f.write("\n\n")
    f.close()


def recheck(salon_id, pretty_date, document, rec_id, lid):
    # print('Запустился речек записи')
    block = check_record(salon_id, pretty_date, document)
    isprint, kkm = check_kkm(salon_id, pretty_date, document)

    if block == True and isprint == "True":
        result = unblock_rec(rec_id)
        # print(f"Result of unblock: {result}")
        pretty_output_second(1, result, 0, 0, salon_id, rec_id, lid)

    elif block == True and isprint == "False":
        # print(f"Больше одной ккм транзакции! Требуется ручное действие\nisblock = {block} and isprint = {isprint}")
        pretty_output_second(2, 0, document, kkm, salon_id, rec_id, lid)

    else:
        # print(f"Анлок не требуется. Причина: isblock = {block} and isprint = {isprint}")
        pretty_output_second(3, 0, block, isprint, salon_id, rec_id, lid)


def datechanger(string):
    truedate = string.split("T")
    return truedate[0]


def check_record(salon_id, date, doc_id):
    url = f"https://api.yclients.com/api/v1/records/{salon_id}?c_start_date={date}&c_end_date={date}"
    response = requests.request("GET", url, headers=headers)
    pretty_respone = response.json()
    isprint = "none"
    for i in range(len(pretty_respone["data"])):
        # print(pretty_respone["data"][i]["documents"][0])
        if pretty_respone["data"][i]["documents"][0]["id"] == doc_id:
            isprint = pretty_respone["data"][i]["is_sale_bill_printed"]
    return isprint


def check_kkm(salon_id, date, doc_id):
    kkm = []
    url = f"https://api.yclients.com/api/v1/kkm_transactions/{salon_id}?start_date={date}&end_date={date}&editable_length=1000"
    response = requests.request("GET", url, headers=headers)
    pretty_response = response.json()
    kkm_status = "none"
    cnt = 0
    trans_type = -1
    for i in range(len(pretty_response["data"])):
        if pretty_response["data"][i]["document_id"] == doc_id:
            cnt += 1
            trans_type = pretty_response["data"][i]["type"]["id"]
            kkm.append(pretty_response["data"][i]["id"])
            kkm_pre_status = pretty_response["data"][i]["status"]["id"]
            # print(trans_type, kkm_pre_status)
    if cnt == 1 and trans_type == 0:
        kkm_status = "True"
    else:
        kkm_status = "False"
    return kkm_status, kkm


def unblock_rec(rec_id):
    url = f"https://yclients.com/tester/unlock_record/{rec_id}"
    response = requests.request("GET", url, headers=u_headers)
    return response.text


@app.route('/log')
def log():
    # print(request)
    f = open('log.txt', 'r')
    text = f.read()
    # print(text)
    # print(text)

    # with open('log.txt',"r") as f:
    #     for line in f.readlines():
    #         print(line)

    return f'''<h3> Log </h3>{text}
<p style="font-size:12px; color: #49456a"> 
Это актуальные логи. Архив можно посмотреть  <a href="/log_2">здесь</a></p>
'''


@app.route('/log_2')
def log2():
    # print(request)
    f = open('log_2.txt', 'r')
    text = f.read()
    # print(text)
    # print(text)

    # with open('log.txt',"r") as f:
    #     for line in f.readlines():
    #         print(line)

    return f'''<h3> Log </h3>{text}
<p style="font-size:12px; color: #49456a"> 
Это архивная страница с логами. Актуальные можно посмотреть <a href="/log">здесь</a></p>
'''


@app.route('/db')
def db():
    # print(request)
    f = open('salon_db.txt', 'r')
    text = f.read()
    # print(text)
    # print(text)

    # with open('log.txt',"r") as f:
    #     for line in f.readlines():
    #         print(line)

    return f'''<h3> Salons </h3>{text}'''


if __name__ == '__main__':
    app.run(debug=True, port=2500)
