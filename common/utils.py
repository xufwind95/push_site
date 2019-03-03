import random
import string
import datetime
import json
from threading import Lock


DEFAULT_CHAR_STRING = string.ascii_lowercase + string.digits


def generate_random_string(chars=DEFAULT_CHAR_STRING, size=6):
    return ''.join(random.choice(chars) for _ in range(size))


lock = Lock()
start = datetime.datetime.now()
sequence = {
    "seq": 1,
    'time_tuple': (start.year, start.month, start.day, start.hour, start.minute, start.second)
}


def gen_order_sequence():
    """ 生成订单序列号
    :return: 序列号的字符串形式
    """
    with lock:
        now = datetime.datetime.now()
        now_tuple = (now.year, now.month, now.day, now.hour, now.minute, now.second)
        last = sequence['time_tuple']
        seq = sequence['seq'] + 1
        time_tuple = sequence['time_tuple']
        if now_tuple != last:
            seq = 1
            time_tuple = now_tuple
        sequence.update(
            {
                'seq': seq,
                'time_tuple': time_tuple,
            }
        )
    # 订单号规则: 年月日时分秒+2位随机数+两位序列号
    # 18 11 30 23 59 59 23 23
    year = now_tuple[0] % 100
    # now_tuple = now_tuple[1:]
    rand_num = random.randrange(10, 100)
    order_seq = '{0:02}{1:02}{2:02}{3:02}{4:02}{5:02}{6:02}{7:02}'.format(
        year,
        now_tuple[1],
        now_tuple[2],
        now_tuple[3],
        now_tuple[4],
        now_tuple[5],
        rand_num,
        seq,
    )
    return order_seq


def get_desc_from_lang_desc_map(desc_str, lang_type):
    """ 根据传入的以语言类型为key的描述信息，获取对应语言的描述信息
    能找到对应的大语言类型的，返回对应语言，不能的找英语，英语也没有的返回空
    :param desc_str: 要求key为 en, ar, zh 这种大的语言类型！ 且为json字符串
    :param lang_type:
    :return:
    """
    try:
        desc_map = json.loads(desc_str)
    except json.decoder.JSONDecodeError:
        return None
    # 检查数据类型
    assert type(desc_map) == dict, 'type of desc_map is not map'
    assert type(lang_type) == str, 'type of lang_type is not str'

    desc_en = None
    for it_lang in desc_map:
        if lang_type.upper().startswith(it_lang.upper()):
            return desc_map[it_lang]
        if it_lang.upper() == 'EN':
            desc_en = desc_map[it_lang]
    return desc_en
