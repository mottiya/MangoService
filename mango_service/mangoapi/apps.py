from django.apps import AppConfig


class MangoapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mangoapi'

    mango_url = 'https://app.mango-office.ru/vpbx'
    JW_url = 'https://tgbsrv.joywork.ru/trend_webhook.php'

    # callback_path = mango_url + '/commands/callback'
    add_task_path = mango_url + '/task/add'
    campaign_id = 1407511

    worker_extention_path = mango_url + '/config/users/request'

    callback_id_prefix = 'avito'
    robot_extension = '15'

    mango_salt = '......'
    mango_api_key = '.......'

    JW_key = '......'

    robot_extension_baza = ['18', '19', '20']
    task_url = mango_url + '/task'
    user_token_nedozvon = '......'
