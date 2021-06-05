
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io
import base64

from flask import Flask
app = Flask(__name__)

html = '''
<html>
    <body>
        <img src="data:image/png;base64,{}" />
    </body>
</html>
'''

@app.route("/")
def hello():
    df = pd.DataFrame(
        {'y':np.random.randn(10), 'z':np.random.randn(10)},
        index=pd.period_range('1-2000',periods=10),
    )
    plt.close('all')
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    df.plot(ax=ax)

    img = io.BytesIO()
    fig.savefig(img, format='png')
    data = base64.encodestring(img.getvalue()).decode('utf-8')

    return html.format(data)


if __name__ == '__main__':
    app.run()
