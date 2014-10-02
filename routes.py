#!/cygdrive/d/canopy/User/Scripts/python
from flask import Flask, render_template, request, jsonify
#from pymysql.cursors import DictCursor
import pymysql as mdb
import cPickle as pickle
import re
from load_db import DB

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
	db = DB()
	cur = db.cursor
	cur.execute("""SELECT hll.hotel_name, hotel_name_pretty, lng, lat
		         FROM hotellnglat hll 
		   INNER JOIN hotelnames hn 
		           ON hll.hotel_name = hn.hotel_name""")
	query_results = cur.fetchall()

	hotelblurb = []; hotelnames = []
	hotellng = []; hotellat = []
	for entry in query_results:
		hotellng.append(entry['lng'])
		hotellat.append(entry['lat'])
		hotel_name_pretty=str(entry['hotel_name_pretty'])
		hotelnames.append(hotel_name_pretty)
		temp = str(entry['hotel_name'])
		blurb = ('<div class="blurb"><img src="../static/imgs/logo-01.png" height="25">:&nbsp;<a href=/hotel/' 
                         + temp + '>' + hotel_name_pretty + '</a></div>')
		hotelblurb.append(blurb)
	return render_template("index.html", hotelnames=hotelnames, hotellng=hotellng, hotellat=hotellat, hotelblurb=hotelblurb)


@app.route("/hotel/<hotelname>")
def results(hotelname):
	db = DB()
	cur = db.cursor
	
	# Retrieve the hotel terms information
	cur.execute("""SELECT term_id, term_name, term_count, percent_pos, bigram, trend_score, class 
			 FROM hotelterms ht 
		   INNER JOIN hotelnames hn ON ht.hotel_name = hn.hotel_name 
		        WHERE hn.hotel_name = %s AND term_doc_freq >= 5 
		     ORDER BY term_count DESC""", hotelname)
	query_results = cur.fetchall()
	
	# Process the sentiment
	terms = []
	for entry in query_results:
		pos_sentiment = float(entry['percent_pos'])
		if pos_sentiment >= 50:
			start = 49.6
			end = pos_sentiment - start - 0.8
		else:
			start = pos_sentiment
			end = 49.6 - pos_sentiment

		if str(entry['class'].strip()) == 'None':
		    label = None
		else:
			label = '../static/imgs/' + str(entry['class'])
		terms.append(dict(term_id=int(entry['term_id']), term_name=entry['term_name'], 
				  bigram=entry['bigram'], term_count=entry['term_count'], 
			          start=start, end=end, trend_score="%.02f" %entry['trend_score'], 
				  label=label, pos_sentiment=pos_sentiment))

	# Retrieve hotel rating information
	cur.execute("""SELECT * 
		  	 FROM hotelnames 
		   	WHERE hotel_name = %s""", hotelname)
	query_results = cur.fetchone()

	starimage = "../static/imgs/star%.1f.png" %query_results['avg_star']
	hotel = dict(hotelid=query_results['hotel_id'], hotelnamepretty=query_results['hotel_name_pretty'], 
		     numreviews=query_results['num_reviews'], hotelname=hotelname)
	stars = {}
	for i in range(1, 6):
		key = "%d_star" %i
		stars[i] = {}
		stars[i]['count'] = query_results[key]
		stars[i]['fraction'] = 100.0*query_results[key]/query_results['num_reviews']

	# Retrieve booking link for the hotel
	cur.execute("""SELECT hotel_link 
		         FROM hotellinks 
		        WHERE hotel_name = %s""", hotelname)
	hotel['booking'] = cur.fetchone()['hotel_link']

	# Retrieve longitude and latitude for the hotel
	cur.execute("""SELECT lng, lat
		         FROM hotellnglat hll 
		        WHERE hotel_name = %s""", hotelname)
	query_results = cur.fetchone()
	hotel['lng'] = query_results['lng']
	hotel['lat'] = query_results['lat']
	return render_template('result.html', data=terms, hotel=hotel, starimage=starimage, stars=stars) 


@app.route("/sentences", methods=['GET'])
def get_sentences():
	hotelid = request.args.get('hotelid', type=int)
	termid = request.args.get('termid', type=int)
	termname = request.args.get('termname', type=str)

	# Retrieve the sentence ids for the hotel term
	db = DB()
	cur = db.cursor
	cur.execute("""SELECT sent_id 
		         FROM hotelnames hn 
		   INNER JOIN hotelterms ht ON ht.hotel_name = hn.hotel_name 
		   INNER JOIN mapping m ON ht.hotel_name = m.hotel_name AND ht.term_id = m.term_id 
		        WHERE hn.hotel_id = %s AND ht.term_id = %s""", (hotelid, termid))
	query_results = cur.fetchall()
	sent_ids = ""
	for entry in query_results:
		sent_ids += '"'
		sent_ids += str(entry['sent_id'].strip())
		sent_ids += '",'

		
	# Retrieve the sentences for the hotel term
	cur.execute("""SELECT month, year, sentence FROM sentences 
			WHERE sent_id IN (%s) 
		     ORDER BY year DESC, month DESC""" %sent_ids[:-1])
	query_results = cur.fetchall()
	
	# Format the sentences
	data = {}
	data[0] = ""
	replacement = "<b>" + termname + "</b>"
	for entry in query_results:
		# Format the date
		data[0] += '<div align=right class="modal-text">date: '
		data[0] += '<i><b>%02d-%d</b></i></div>' %(entry['month'], entry['year'])
		data[0] += '<div class="modal-text">'
		
		# Format the sentence
		sent = str(entry['sentence'])
		sent = sent.replace(" " + termname, " " + replacement)
		if sent[:len(termname)] == termname:
			sent = replacement + sent[len(termname):]
		data[0] += sent 
		data[0] += "<br/><br/>"
	data[0] += '</div>'
	return jsonify(data)
	

@app.route("/chord/<hotelname>")
def chord(hotelname):
	return render_template('chord.html', hotelname=hotelname)

@app.route("/slides")
def slides():
	return render_template('slides.html')

@app.route("/about")
def about():
	return render_template('about.html')

@app.route("/graph/<hotelname>")
def graph(hotelname):
	db = DB()
        cur = db.cursor
        cur.execute("""SELECT * FROM nodes WHERE hotel_name = %s""", hotelname)
	query_results = cur.fetchall()

	nodes = []
	for entry in query_results:
		node = {}
		node['id'] = entry['id']
		node['label'] = str(entry['label'].strip())
		nodes.append(node)

	cur.execute("""SELECT * FROM edges WHERE hotel_name = %s""", hotelname)
	query_results = cur.fetchall()
	edges = []
	for entry in query_results:
		edge = {}
		edge['to'] = entry['e_to']
		edge['from'] = entry['e_from']
		edge['value'] = float(entry['value'])
		edge['title'] = "npmi = " + str(entry['value'])
		edges.append(edge)
	return render_template('graph.html', nodes=nodes, edges=edges)
	
	
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)
