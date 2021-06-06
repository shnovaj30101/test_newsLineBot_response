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
from sqlalchemy_fulltext import FullText, FullTextSearch
import sqlalchemy_fulltext.modes as FullTextMode
import base64
import numpy as np
import re
import json
from database import session_executor
import models
from database import engine

app = Flask(__name__)

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
            if 'keyword' in query_db_info:
                with session_executor() as db_session:
                    session.query(News).filter(FullTextSearch(query_db_info['keyword'], News, FullTextMode.NATURAL))

            return {
                'response_text': 'query_db_info:{0}\ndisplay_info:{1}'.format(
                    json.dumps(query_db_info, ensure_ascii = False),
                    json.dumps(display_info, ensure_ascii = False)
                    ),
            }


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

