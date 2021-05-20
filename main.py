from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
from flask import Flask, request, render_template
import pymongo
import time


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def homepage():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    my_database = 'FlipkartReviews'

    con = pymongo.MongoClient('mongodb://localhost:27017/')
    database_list = con.list_database_names()

    db = con[my_database]

    collection_list = db.list_collection_names()
    search_string = request.form['search']

    if search_string in collection_list:
        collection = db[search_string]
        new_list = list(collection.find({}))
        return render_template('index.html', response=new_list, num_of_results=len(new_list))
    else:
            print('Database Not Found! Creating One.')
            db = con[my_database]

            flipkart_url = "https://www.flipkart.com/search?q=" + search_string

            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()

            flipkart_html = bs(flipkartPage, 'html.parser')
            bigboxes = flipkart_html.findAll("a", {"class": "_1fQZEK"})

            product_list = []

            for i in bigboxes:
                product_list.append(i['href'])

            print('Length of Product List -> ', len(product_list))

            new_list = []
            count = 1
            page = 1
            for product in product_list[:10]:
                product_link = "http://www.flipkart.com" + product

                prodRes = uReq(product_link)
                product_page = prodRes.read()
                prodRes.close()

                prod_html = bs(product_page, 'html.parser')

                comment_box = prod_html.find_all('div', {'class': '_16PBlm'})
                print('Page Number : ', page)
                page += 1
                try:
                    del comment_box[-1]
                    collection = db[search_string]

                    for comment in comment_box:
                        name = comment.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                        rating = comment.find_all('div', {'class': '_3LWZlK _1BLPMq'})[0].text
                        comment_head = comment.find_all('p', {'class': '_2-N8zT'})[0].text
                        description = comment.find_all('div', {'class': 't-ZTKy'})[0].div.div.text

                        mydict = dict(count=count, name=name, rating=rating, commentHead=comment_head,
                                      description=description)

                        collection.insert_one(mydict)

                        new_list.append(mydict)
                        print('count -> ', count)
                        count += 1
                except IndexError:
                    pass

                time.sleep(5)

            return render_template('index.html', response=new_list, num_of_results=len(new_list))


if __name__ == '__main__':
    app.run(debug=True)

