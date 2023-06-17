import requests
from flask import Flask
from flask import request
from config import headers

app = Flask(__name__)


@app.route('/')
def hello():
    print(request)
    return 'собака 2 сутулая'


# allow both GET and POST requests
@app.route('/unlock', methods=['GET', 'POST'])
def form_example():
    # handle the POST request
    cnt = 0
    if request.method == 'POST':
        inputdata = request.form.get('URL')
        cnt += 1
        salon_and_rec = clearurl(inputdata)
        print("POST #", cnt)
        print("salon_id, rec_id:")
        print(salon_and_rec[0], salon_and_rec[1])
        print("document, date:")
        document = get_document(salon_and_rec[0], salon_and_rec[1])
        print(document)
        print("kkm_id:")
        kkm_id = get_kkm_id(salon_and_rec[0], document[0], document[1], document[2])
        print(kkm_id)
        print("summary: ")
        print(f"UPDATE documents SET bill_print_status = 1 WHERE id = {document[0]};")
        print(f"UPDATE kkm_transactions SET status = 3 WHERE id = {kkm_id};")

        return '''<h1>OK</h1>
                  <p>UPDATE documents SET bill_print_status = 1 WHERE id = {0};</p>
                  <p>UPDATE kkm_transactions SET status = 3 WHERE id = {1};</p>
                  <a href = "/unlock"> Обновить страницу  </a>
                  '''.format(document[0], kkm_id)

    return '''
              <form method="POST">
              <p> Ссылка в виде https://yclients.com/timetable/493251#main_date=2023-01-28&open_modal_by_record_id=569963743 
              <b>ОБЯЗАТЕЛЬНО</b> </p>
                  <div>Вставь ссылку на запись <input type="text" name="URL"></label></div>
                  <input type="submit" value="Submit">
              </form>'''


def clearurl(data):
    # print("URL IS: ", data)
    newstr = data.split("/")
    newstr[-1] = newstr[-1].split("#")
    salon_id = int(newstr[-1][0])
    rec_id_dirt = newstr[-1][-1].split("=")
    rec_id = int(rec_id_dirt[-1])
    return salon_id, rec_id


def get_document(salon_id, record_id):
    url = f"https://api.yclients.com/api/v1/record/{salon_id}/{record_id}"
    response = requests.request("GET", url, headers=headers)
    response_clean = response.json()

    document = response_clean["data"]["documents"][0]["id"]
    c_date = response_clean["data"]["create_date"]
    v_date = response_clean["data"]["datetime"]
    c_date_pretty = c_date.split("T")
    v_date_pretty = v_date.split("T")
    new_date = c_date_pretty[0]
    end_date = v_date_pretty[0]
    # print(document, new_date)
    return document, new_date, end_date


def get_kkm_id(salon_id, doc_id, date, enddate):
    url = f"https://api.yclients.com/api/v1/kkm_transactions/{salon_id}?start_date={date}&end_date={enddate}&editable_length=1000"
    payload = {}
    response = requests.request("GET", url, headers=headers)
    pretty_response = response.json()
    kkm_id = 1
    cnt = 0
    listofid = []
    for i in range(len(pretty_response["data"])):
        if pretty_response["data"][i]["document_id"] == doc_id:
            # print("Step ", i)
            # print(cnt, kkm_id, listofid)
            cnt += 1
            if cnt > 1:
                listofid.append(pretty_response["data"][i]["id"])
            else:
                kkm_id = pretty_response["data"][i]["id"]
    listofid.append(kkm_id)
    max_kkm = max(listofid)
    return max_kkm


#
# document = get_document(salon_id, 572948924)
# kkm_id = get_kkm_id(764917,document[0],document[1])
#
# print(f"UPDATE documents SET bill_print_status = 1 WHERE id = {document[0]};")
# print(f"UPDATE kkm_transactions SET status = 3 WHERE id = {kkm_id};")


if __name__ == '__main__':
    app.run()
