from flask import Flask, render_template, request
import io
import random
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pymysql
import base64
import numpy as np

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    cmd = request.json['cmd']
    print(cmd)

    if cmd == 'test_plot':
        img = create_img()
        data = base64.encodestring(img.getvalue()).decode('utf-8')
        return {
            'response_img_data': data,
        }


    return {
        'response_text': cmd,
    }

def create_img():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    x_points = range(50)
    axis.plot(x_points, [random.randint(1, 30) for x in x_points])

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return output

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run()

