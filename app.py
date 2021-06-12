from flask import Flask, render_template, request
import io
import random
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pymysql
from datetime import datetime, timedelta
pymysql.install_as_MySQLdb()
from sqlalchemy import or_, and_
import base64
import numpy as np
import re
import json
from database import session_wrapper
import models
from database import engine
from models import News
import math
from datetime import timedelta
from matplotlib.font_manager import FontProperties

font = FontProperties(fname="./font/NotoSerifCJKtc-Light.otf", size=14)
'''
下載方法：
https://daxpowerbi.com/%E5%A6%82%E4%BD%95%E5%9C%A8win-10%E8%A7%A3%E6%B1%BAmatplotlib%E4%B8%AD%E6%96%87%E9%A1%AF%E7%A4%BA%E7%9A%84%E5%95%8F%E9%A1%8C/
'''

app = Flask(__name__)


START_FORMAT = '''SELECT {0} FROM news_table WHERE '''
FULLTEXT_SEARCH_FORMAT = '''MATCH (`{0}`, `{1}`) AGAINST ('{2}' IN BOOLEAN MODE)'''

@app.route("/callback", methods=['POST'])
def callback():
    cmd = request.json['cmd']
    cmd = cmd.strip()
    print(cmd)

    if cmd == 'test_plot':
        return get_test_plot_response()
    elif cmd == 'u' or cmd == 'url':
        return get_url_response()
    elif cmd == 'man' or cmd == 'manual':
        return get_manual_response()
    else:
        query_db_info = {}
        display_info = {}
        success = parse_all_cmd(cmd, query_db_info, display_info)

        if not success:
            return get_unknown_cmd_response()

        else:
            query_result = exec_session_query(query_db_info)

            if 'show_num' in query_db_info: # todo
                return {
                    'response_text': 'query_db_info:{0}\ndisplay_info:{1}'.format(
                        json.dumps(query_db_info, ensure_ascii = False),
                        json.dumps(display_info, ensure_ascii = False)
                        ),
                }
            else:
                return get_statistic_figure_response(query_result, query_db_info, display_info)


def get_statistic_figure_response(query_result, query_db_info, display_info):
    if len(query_result) == 0:
        return {
            'response_text': 'No data result\nquery_db_info:{0}\ndisplay_info:{1}'.format(
                json.dumps(query_db_info, ensure_ascii = False),
                json.dumps(display_info, ensure_ascii = False)
                ),
        }
    all_day_num = (query_result[-1]['post_time'] - query_result[0]['post_time']).days + 1

    if all_day_num/display_info['days_unit'] > 30:
        display_info['days_unit'] = math.ceil(all_day_num/30)
    # print('all_day_num', all_day_num)
    # print('display_info["days_unit"]', display_info["days_unit"])

    stat_info = [{
            'date': query_result[0]['post_time'],
            'count': 0,
        }]

    for result_item in query_result:
        while (result_item['post_time'] - stat_info[-1]['date']).days + 1 > display_info['days_unit']:
            stat_info.append({
                'date': stat_info[-1]['date'] + timedelta(days=display_info['days_unit']),
                'count': 0,
                })

        stat_info[-1]['count'] += 1

    # print(stat_info)

    fig = Figure(figsize=(9,6))
    # reference: https://matplotlib.org/3.3.4/api/_as_gen/matplotlib.figure.Figure.html
    axis = fig.add_subplot(1, 1, 1)
    if 'keyword' not in query_db_info:
        axis.set_title("統計結果(keyword:None)", fontproperties=font)
    else:
        axis.set_title("統計結果(keyword:{0})".format(query_db_info['keyword']), fontproperties=font)

    axis.set_xlabel('日期', fontproperties=font)
    axis.set_ylabel('新聞數', fontproperties=font)
    # axis.set_xticklabels([ stat_item['date'].strftime('%Y%m%d') for stat_item in stat_info], rotation=45, ha='right')
    axis.set_xticklabels([ stat_item['date'].strftime('%Y%m%d') for stat_item in stat_info], rotation=90)
    # reference: https://www.delftstack.com/zh-tw/howto/matplotlib/how-to-rotate-x-axis-tick-label-text-in-matplotlib/
    axis.bar([ stat_item['date'].strftime('%Y%m%d') for stat_item in stat_info], [ stat_item['count'] for stat_item in stat_info])

    fig.tight_layout()

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    data = base64.encodestring(output.getvalue()).decode('utf-8')

    return {
        'response_img_data': data,
        'response_text': 'query_db_info:{0}\ndisplay_info:{1}'.format(
            json.dumps(query_db_info, ensure_ascii = False),
            json.dumps(display_info, ensure_ascii = False)
            ),
    }

def exec_session_query(query_db_info):
    with session_wrapper() as session:
        if 'show_num' in query_db_info: # todo
            pass
        else:
            if 'keyword' in query_db_info:
                start_cmd = START_FORMAT.format("`{0}`,`{1}`".format('post_time', 'news_id'))
                constraint_cmd_list = []
                constraint_cmd_list.append(FULLTEXT_SEARCH_FORMAT.format('title', 'content', query_db_info['keyword']))
                if 'date_range' in query_db_info:
                    if 'start' in query_db_info['date_range'] and 'end' in query_db_info['date_range']:
                        date_range_cmd = "`post_time` BETWEEN '{0}' AND '{1}'".format(query_db_info['date_range']['start'], query_db_info['date_range']['end'])
                    elif 'start' in query_db_info['date_range']:
                        date_range_cmd = "`post_time` >= '{0}'".format(query_db_info['date_range']['start'])
                    elif 'end' in query_db_info['date_range']:
                        date_range_cmd = "`post_time` <= '{0}'".format(query_db_info['date_range']['end'])

                    constraint_cmd_list.append(date_range_cmd)

                sort_cmd = ' ORDER BY `{0}`'.format('post_time')

                merged_cmd = start_cmd + ' AND '.join(constraint_cmd_list) + sort_cmd
                merged_cmd += ';'

                query_result = session.execute(merged_cmd)
                # return query_result.mappings()
                return query_result.mappings().all()

            else:
                query = session.query(News.news_id, News.post_time)
                if 'date_range' in query_db_info:
                    if 'start' in query_db_info['date_range']:
                        query = query.filter(News.post_time >= query_db_info['date_range']['start'])
                    if 'end' in query_db_info['date_range']:
                        query = query.filter(News.post_time <= query_db_info['date_range']['end'])

                query = query.order_by(News.post_time)

                # return map(lambda x: x._asdict(), query)
                return list(map(lambda x: x._asdict(), query))


def parse_keyword(text, query_db_info, display_info):
    if text.startswith('k:'):
        text = text[2:]

    query_db_info['keyword'] = text

    return True

def parse_show_num(text, query_db_info, display_info):
    show_num = int(text.split(' ')[1])

    if show_num > 20:
        show_num = 20

    display_info['show_num'] = show_num
    query_db_info['show_num'] = show_num

    return True

def parse_source(text, query_db_info, display_info):
    if text is None:
        return True
    return True

def parse_date(text, query_db_info, display_info):
    now_date = datetime.now()

    text_part_list = text.split(':')

    if not (len(text_part_list) == 1 or len(text_part_list) == 2):
        return False

    if len(text_part_list) == 1:
        date_part, other_part = text_part_list[0], None

    if len(text_part_list) == 2:
        date_part, other_part = text_part_list

    if date_part == 'm' or date_part == 'month':
        query_db_info['date_range'] = {
                'end': now_date.strftime('%Y/%m/%d'),
                'start': (now_date - timedelta(days=30)).strftime('%Y/%m/%d'),
                }

    if date_part == 'w' or date_part == 'week':
        query_db_info['date_range'] = {
                'end': now_date.strftime('%Y/%m/%d'),
                'start': (now_date - timedelta(days=7)).strftime('%Y/%m/%d'),
                }

    if re.search('^\d{8}-\d{8}', date_part):
        start_date_str, end_date_str = date_part.split('-')
        query_db_info['date_range'] = {
                'end': datetime.strptime(end_date_str, '%Y%m%d').strftime('%Y/%m/%d'),
                'start': datetime.strptime(start_date_str, '%Y%m%d').strftime('%Y/%m/%d'),
                }

    if re.search('^\d{8}~\d{8}', date_part):
        start_date_str, end_date_str = date_part.split('~')
        query_db_info['date_range'] = {
                'end': datetime.strptime(end_date_str, '%Y%m%d').strftime('%Y/%m/%d'),
                'start': datetime.strptime(start_date_str, '%Y%m%d').strftime('%Y/%m/%d'),
                }

    display_info['days_unit'] = 1

    if other_part is not None:
        if other_part.isnumeric():
            display_info['days_unit'] = int(other_part)
        else:
            return False

    return True

def parse_all_cmd(cmd, query_db_info, display_info):
    if cmd == 'm' or cmd == 'month' or \
        cmd == 'w' or cmd == 'week' or \
        cmd.startswith('m:') or cmd.startswith('month:') or \
        cmd.startswith('w:') or cmd.startswith('week:') or \
        re.search('^\d{8}-\d{8}', cmd) or \
        re.search('^\d{8}~\d{8}', cmd):

        return parse_date(cmd, query_db_info, display_info)

    cmd_part_list = cmd.split(';;')

    if len(cmd_part_list) == 1:
        cmd_part_list.append('month')
    if len(cmd_part_list) == 2:
        cmd_part_list.append(None)

    if re.search('^s \d+', cmd_part_list[1]) or re.search('^show \d+', cmd_part_list[1]):
        return parse_keyword(cmd_part_list[0], query_db_info, display_info) and \
                parse_show_num(cmd_part_list[1], query_db_info, display_info) and \
                parse_source(cmd_part_list[2], query_db_info, display_info)

    else:
        return parse_keyword(cmd_part_list[0], query_db_info, display_info) and \
                parse_date(cmd_part_list[1], query_db_info, display_info) and \
                parse_source(cmd_part_list[2], query_db_info, display_info)


def get_test_plot_response():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(50)
    axis.plot(x_points, [random.randint(1, 30) for x in x_points])

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    data = base64.encodestring(output.getvalue()).decode('utf-8')
    return {
        'response_img_data': data,
    }

def get_url_response():
    return {
        'response_text': "給你一個神祕的url ><",
    }

def get_manual_response():
    return {
        'response_text': "我還沒把使用手冊生出來QQ",
    }

def get_unknown_cmd_response():
    return {
        'response_text': "我不知道你要我幹嘛OAO",
    }

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run()

