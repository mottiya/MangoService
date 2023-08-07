from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from .apps import MangoapiConfig
import requests
import json
from hashlib import sha256
from django.http import Http404
import time
import csv
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

def get_mango_post_data(dict_json:str):
    json_data = json.dumps(dict_json)
    string = bytes(MangoapiConfig.mango_api_key + json_data + MangoapiConfig.mango_salt, encoding='utf-8')
    sign = sha256(string=string).hexdigest()
    data={'vpbx_api_key':MangoapiConfig.mango_api_key,
          'sign': sign,
          'json': json_data}
    return data

def try_request(url, data=None, json=None) -> requests.Response:
    print('try_request', url, data, json, sep='\n')
    for t in range(7):
        response = requests.post(url=url, data=data, json=json)
        if response.status_code == 200:
            return(response)
        print(f"sleep {2**t} seconds")
        time.sleep(2**t)
    raise Exception(f"request failed {response.status_code}")    

class AdvertCreateAPIView(views.APIView):

    def get(self, request):
        # print(next(MangoapiConfig.get_line_generator))
        adverts = Advert.objects.all()
        serializer = AdvertSerialaizer(adverts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = AdvertSerialaizer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                response = AdvertCreateAPIView.s_mango_create_call_request(serializer.instance)
                if response['result'] == 1000:
                    serializer.instance.task_id = response['task_id']
                    serializer.save()
                    print('Update model advert')
                else:
                    print(f'Create call EXCEPTION {response}')
            except Exception as err:
                print(err)
                return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def s_mango_create_call_request(model):
        # data = {
        #     "command_id": MangoapiConfig.callback_id_prefix + model.id_avito,
        #     "from": {
        #         "extension": MangoapiConfig.robot_extension
        #     },
        #     "to_number": model.tel,
        #     # "line_number": MangoapiConfig.main_line,
        # }
        data = {
            "campaign_id": MangoapiConfig.campaign_id,
            "number": model.tel,
            "comment": f"From Avito id {model.id_avito}, link {model.link}"
        }
        response_json = try_request(url=MangoapiConfig.add_task_path, data=get_mango_post_data(data)).json()
        print(response_json)
        return response_json

class CallCreateAPIView(views.APIView):

    def get(self, request):
        call = Call.objects.all()
        serializer = CallSerialaizer(call, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 

    def post(self, request):
        data = json.loads(request.data['json'])
        serializer = CallSerialaizer(data=data)
        if serializer.is_valid():
            serializer.save()
            if not CallCreateAPIView.s_save_or_hold_callback_avito(serializer.instance):
                CallCreateAPIView.s_save_or_hold_callback_baza_nedozvon(serializer.instance)
                CallCreateAPIView.s_save_or_hold_callback_baza_manager(serializer.instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def s_save_or_hold_callback_baza_nedozvon(call_model:Call) -> bool:
        if call_model is None:
            return False
        if call_model.task_id is None:
            return False
        if call_model.call_state != "Disconnected":
            return False
        if CallCreateAPIView.is_task_nedozvon(call_model.task_id):
            CallCreateAPIView.s_JW_request(JW_user_token=MangoapiConfig.user_token_nedozvon,
                                           funnel_id=543, #покупатель
                                           type_id=1, #подбор обьекта
                                           source_id=1885, #Общие
                                           phone=call_model.from_user.number,
                                           name="Спрос по нашему обьекту",
                                           about='',
                                           general_req=1) # reverse call; from == to
        
    def is_task_nedozvon(task:str) -> bool:
        task_info = CallCreateAPIView.get_task_info(task)
        print('task_info: ', task_info)
        try:
            if task_info["task"]["status"] == 4: #завершен
                if task_info["task"]["status_reason"] in [2, 3, 4, 21, 22, 23]: return True #коды результатов
                if task["task"]["subtasks"] is not None:
                    sub_task_id_list = [i["subtask_id"] for i in task["task"]["subtasks"]]
                    for sub_task_id in sub_task_id_list:
                        sub_task_info = CallCreateAPIView.get_task_info(sub_task_id)
                        print('sub_task_info: ', sub_task_info)
                        if sub_task_info["task"]["status"] == 4:
                            if sub_task_info["task"]["status_reason"] in [2, 3, 4, 21, 22, 23]: return True #коды результатов
        except (IndexError, KeyError):
            print(f"get_task_info EXCEPTION: {task}; IndexError: {task_info}")
        return False
    
    def get_task_info(task:str):
        data = {
            "task_id": task,
        }
        post_data = get_mango_post_data(data)
        response = try_request(url=MangoapiConfig.task_url, data=post_data).json()
        return response

    def s_save_or_hold_callback_baza_manager(call_model:Call) -> bool:
        if call_model is None:
            return False
        if call_model.task_id is None:
            return False
        if call_model.from_user.extension in MangoapiConfig.robot_extension_baza:
            return False
        if call_model.to_user.extension in MangoapiConfig.robot_extension_baza:
            return False
        if call_model.call_state == "Connected":
            if call_model.to_user.extension:
                position_worker_list = CallCreateAPIView.s_get_id_worker_list(call_model.to_user.extension)# [positions, names]
                if len(position_worker_list[0]) == 0:
                    return False
                token_name_list = []
                for i in range(len(position_worker_list[0])):
                    token_name_list.append([position_worker_list[0][i], position_worker_list[1][i]])
                print('token_name_list', token_name_list)
                for t in token_name_list:
                    CallCreateAPIView.s_JW_request(JW_user_token=t[0].split(';')[1].strip(),
                                                   funnel_id=543, #покупатель
                                                   type_id=1, #подбор обьекта
                                                   source_id=1885, #Общие
                                                   phone=call_model.from_user.number,
                                                   name=f"Спрос по нашему обьекту для {t[1].strip()} агент", #для имя менеджера
                                                   about='',
                                                   general_req=0) # reverse call; from == to
            else:
                return False

    def s_save_or_hold_callback_avito(call_model:Call) -> bool:# return true if 
        if call_model is None:
            return False
        if call_model.task_id is None:
            return False
        if call_model.from_user.extension == MangoapiConfig.robot_extension:
            return True
        if call_model.to_user.extension == MangoapiConfig.robot_extension:
            return True
        try:
            bind_advert = Advert.objects.get(task_id=call_model.task_id)
        except Advert.DoesNotExist:
            return False
        if call_model.call_state == "Connected":
            if call_model.to_user.extension: # reverse call; from == to
                position_worker_list = CallCreateAPIView.s_get_id_worker_list(call_model.to_user.extension)[0]
                if len(position_worker_list) == 0:
                    return True
                tg_id = [i.split(";")[0].strip() for i in position_worker_list]
                for i in tg_id:
                    if i:
                        massage = "call: " + call_model.from_user.number + "\navito id: " + bind_advert.id_avito + "\nlink: " + bind_advert.link
                        tg_notifier = TgNotifier(tg_id=i, massage=massage)
                        tg_notifier.save()
                try:
                    JW_user_token = [i.split(";")[1].strip() for i in position_worker_list]
                    for t in JW_user_token:
                        CallCreateAPIView.s_JW_request(JW_user_token=t,
                                                       funnel_id=216, #продажа вторичной
                                                       type_id=2, #реализация обьекта
                                                       source_id=1359, #авито
                                                       phone=call_model.from_user.number,
                                                       name="РоботЛидГен_Авито",
                                                       about=bind_advert.link,
                                                       general_req=0) # reverse call; from == to
                except IndexError:
                    print("NO JW token in user worker position")
                return True
        return False

    def s_JW_request(JW_user_token:str, funnel_id:int, type_id:int, source_id:int, phone:str, name:str, about: str, general_req:int):
        data = {
            "token_user": JW_user_token,
            "token_agency": MangoapiConfig.JW_key,
            "funnel_id": funnel_id,
            "funnel_req_id": funnel_id,#продажа вторичной
            "type_id": type_id, #реализация обьекта
            "source_id": source_id,#авито
            "phone": phone,
            "name": name,
            "about": about,
            "general_req": general_req
        }
        print('JW_data:', data)
        response = try_request(url=MangoapiConfig.JW_url, json=data)
        print('JW_response:', response.json())
    
    def s_get_id_worker_list(extention:str) -> list:
        data = {
            "extension": extention,
        }
        post_data = get_mango_post_data(data)
        response = try_request(url=MangoapiConfig.worker_extention_path, data=post_data)
        position_list = []
        name_list = []
        for user in response.json()["users"]:
            position_list.append(user["general"]["position"])
            name_list.append(user["general"]["name"])

        return [position_list, name_list]

class CallListAPIView(views.APIView):

    def get(self, request):
        calls = Call.objects.all()
        call_serialaizer = CallSerialaizer(calls, many=True)
        return Response(call_serialaizer.data, status=status.HTTP_200_OK)

class CallDeleteAPIView(views.APIView): 

    def delete(self, request, pk):
        try:
            call = Call.objects.get(pk=pk)
        except Call.DoesNotExist:
            raise Http404
        call.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClearDBApiVIew(views.APIView):
    def delete(self, request):
        call = Call.objects.all()
        advert = Advert.objects.all()
        notifier = TgNotifier.objects.all()
        call.delete()
        advert.delete()
        notifier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TaskCreateAPIView(views.APIView):
    
    def post(self, request):
        data = json.loads(request.data['json'])
        try:
            print('task_info: ', data)
            if TaskCreateAPIView.is_task_nedozvon(data):
                task_info = CallCreateAPIView.get_task_info(data["task_id"])
                CallCreateAPIView.s_JW_request(JW_user_token=MangoapiConfig.user_token_nedozvon,
                                               funnel_id=543, #покупатель
                                               type_id=1, #подбор обьекта
                                               source_id=1885, #Общие
                                               phone=task_info["task"]["number"],
                                               name="Спрос по нашему обьекту",
                                               about='',
                                               general_req=1) # reverse call; from == to
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        except (IndexError, KeyError):
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def is_task_nedozvon(data:str) -> bool:
        try:
            if data["status"] == 4: #завершен
                if data["end_reason"] in [2, 3, 4, 21, 22, 23]: return True
        except (IndexError, KeyError):
            print(f"task EXCEPTION: {data}")
        return False
    # {'campaign_id': 1422252, 'task_id': 950227489, 'status': 4, 'end_reason': 23, 'user_id': -1, 'next_attemp_time': None}

class TgNewAPIView(views.APIView):
    
    def get(self, request):
        new_notifiers = TgNotifier.objects.filter(send_flag=False)
        if not new_notifiers.exists():
            return Response(status=status.HTTP_304_NOT_MODIFIED)
        serialaizer = TgNotifierSerializer(new_notifiers, many=True)
        for notifier in new_notifiers:
            notifier.send_flag = True
            notifier.post_time = datetime.now()
            notifier.save()
        return Response(serialaizer.data, status=status.HTTP_200_OK)

class TgStatsAPIView(views.APIView):

    def get(self, request):
        try:
            date = datetime.strptime(request.data['date'], '%d.%m.%Y')
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{date.strftime("%d-%m-%Y")}stats.csv"'},
        )
        writer = csv.writer(response)
        advert = Advert.objects.filter(create_time__date = date.date()) # в эту дату
        notifier = TgNotifier.objects.filter(create_time__date = date.date())
        writer.writerow(["Collected ads per day", "Transferred to managers"])
        writer.writerow([str(advert.count()), str(notifier.count())])
        return response

class TgCSVAPIView(views.APIView):

    def get(self, request):
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{datetime.today()}base.csv"'},
        )
        writer = csv.writer(response)
        advert = Advert.objects.all()
        writer.writerow(["id", "user_name", "advert_name", "link", "id_avito", "post_time", "adress", "detailing", "tel", "source", "create_time"])
        for ad in advert:
            writer.writerow([str(ad.id), ad.user_name, ad.advert_name, ad.link, ad.id_avito, str(ad.post_time), ad.address, ad.detailing, ad.tel, ad.source, str(ad.create_time)])
        return response
