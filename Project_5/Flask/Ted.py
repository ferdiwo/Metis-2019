# minimal example from:
# http://flask.pocoo.org/docs/quickstart/

from flask import Flask,render_template,url_for, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import Recommender
import pickle as pkl


app = Flask(__name__)  # create instance of Flask class


recc = None


@app.route('/', methods=["GET","POST"])  # the site to route to, index/main in this cas
def recommend() -> str:
    """Launchind TED talk recommender
    Returns:
        str: The HTML we want our browser to render.
    """
    """for i in ['Input', 'Number of Results', 'Sort']:
        if i=='Input':
            text1=request.args.get(i, "0")
        elif i=='Number of Results':
            number1=int(request.args.get(i, "0"))
        else:
            sort1=request.args.get(i, "Views")"""

    #text=x_input[0]['Input']
    #number=int(x_input[1]['Number of Results'])
    #sort=x_input[2]['Sort']
    #recc = Recommender.recommendationsystem(text=text1, number=number1,sort=sort1)
    return render_template('recommendation.html',title = 'Recommendation')

@app.route('/recommendations', methods=['POST','GET'])  # the site to route to, index/main in this cas
def recommend1():
    """Shows the recommendations to the user
    """
    for i in ['Input', 'numbers', 'Sort']:
        if i=='Input':
            text1=request.form.get(i, "Sustainability")
            if text1 == "":
                text1='jhgk'
            print('Hello')
            print(text1)
        elif i=='numbers':
            number1=int(request.form.get(i, "0"))
            print(number1)
        else:
            sort1=request.form.get(i, "Views")

    recc = Recommender.recommendationsystem(text=text1, number=number1,sort=sort1)
    return render_template('home.html',title = 'Recommendations', predictions=recc, counts=range(len(recc)))

if __name__ == '__main__':
    app.run(debug=True)
