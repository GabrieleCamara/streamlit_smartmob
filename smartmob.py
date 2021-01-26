import streamlit as st
import pandas as pd
import numpy as np
import psycopg2
import streamlit as st
from streamlit_folium import folium_static
import folium
import json
import time
import datetime

st.set_page_config(
	page_title = "Smart Mobility",
	)

# --- CONEXAO com banco de dados --- #
try:
    conn = psycopg2.connect("dbname = 'smartmob' port = '5432' user= 'usuarioexterno' password = 'usuarioOGLusuarioexterno' host='200.17.225.171' " )
    cursor = conn.cursor()
    conec = 'Conexao ao banco de dados realizada com sucesso'
except:
    conec = 'Erro na conexao com o banco de dados'
st.info(conec)

# --- FUNCOES --- #
# Retorna lista com os tipos de modais do banco de dados
def lista_modal():
	modais = []
	cursor.execute("""SELECT DISTINCT ON(modal)  rota.modal AS modal_ind FROM rota ORDER BY modal ASC;""")
	resposta = cursor.fetchall()
	for modal in resposta:
		if modal[0] == 1:
			modais.append('A pe')
		elif modal[0] == 2:
			modais.append('Bicicleta')
		elif modal[0] == 3:
			modais.append('Onibus')
		elif modal[0] == 4:
			modais.append('Carro')
		else:
			modais.append('Sem modal')
	return modais

# Retorna o estilo da camada modais
def style_mdl(feature):
	return {'color': '#377eb8' if \
            feature['properties']['modal'] == 1 \
				else '#4daf4a' if feature['properties']['modal'] == 2 
				else '#984ea3' if feature['properties']['modal'] == 3 
				else '#ff7f00' if feature['properties']['modal'] == 4 else '#999999'}

# Retorna o estilo da camada tema ruído sonoro
def style_tm_db(feature):
	return {'color': '#1a9641' if \
            feature['properties']['db_medio'] < 55 \
				else '#fdae61' if 55 < feature['properties']['db_medio'] < 70 else '#d7191c'}

# Retorna o estilo da camada tema velocidade
def style_tm_veloc(feature):
	return {'color': '#fee5d9' if \
            feature['properties']['veloc_medio'] < 5 \
				else '#fcae91' if 5 < feature['properties']['veloc_medio'] < 25 
				else '#fb6a4a' if 25 < feature['properties']['veloc_medio'] < 50 
				else '#de2d26' if 50 < feature['properties']['veloc_medio'] < 80 else '#a50f15'}

# Função que executa as consultas com relação aos modais (individual)
def func_mdl(slc_mdl):
	# --- MODAIS --- #
	if len(slc_mdl) == 0:
		pass
	elif len(slc_mdl) == 1:
		cursor.execute("""CREATE OR REPLACE VIEW rota_modal_selec AS SELECT rotas_filtradas.* FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %slc_mdl[0])
		cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal) As l)) As properties FROM rota_modal_selec As lg   ) As f )  As fc;""")
		json_mdl = json.dumps(cursor.fetchall())
		# Tabela com informacoes dos dados do mapa
		tbl = pd.read_sql_query("SELECT rotas_filtradas.id_rota as id, rotas_filtradas.dia as data FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %slc_mdl[0], conn)
		#st.json(json_mdl[2:len(json_mdl)-2])
		conn.commit()
		if show_tbls:
			tbl
		lyr_mdl = folium.GeoJson(
			json_mdl[2:len(json_mdl)-2],
			name = 'Layer Modais',
			popup = folium.GeoJsonPopup(fields = ['modal']),
			style_function = lambda feature: style_mdl(feature),
    	).add_to(m)
	elif len(slc_mdl) == 2:
		cursor.execute("""CREATE OR REPLACE VIEW rota_modal_selec AS SELECT rotas_filtradas.* FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' 
		UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1]))
		cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal) As l)) As properties FROM rota_modal_selec As lg   ) As f )  As fc;""")
		json_mdl = json.dumps(cursor.fetchall())
		# Tabela com informacoes dos dados do mapa
		tbl = pd.read_sql_query("""SELECT rotas_filtradas.id_rota as id, modais.nm_modal as modal, rotas_filtradas.dia as data FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1]), conn)
		conn.commit()
		if show_tbls:
			tbl
		lyr_mdl = folium.GeoJson(
			json_mdl[2:len(json_mdl)-2],
			name = 'Layer Modais',
			style_function = lambda feature: style_mdl(feature),
    	).add_to(m)
	elif len(slc_mdl) == 3:
		cursor.execute("""CREATE OR REPLACE VIEW rota_modal_selec AS SELECT rotas_filtradas.* FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' 
		UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1], slc_mdl[2]))
		cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal) As l)) As properties FROM rota_modal_selec As lg   ) As f )  As fc;""")
		json_mdl = json.dumps(cursor.fetchall())
		# Tabela com informacoes dos dados do mapa
		tbl = pd.read_sql_query("""SELECT rotas_filtradas.id_rota as id, modais.nm_modal as modal, rotas_filtradas.dia as data FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1], slc_mdl[2]), conn)
		conn.commit()
		if show_tbls:
			tbl
		lyr_mdl = folium.GeoJson(
			json_mdl[2:len(json_mdl)-2],
			name = 'Layer Modais',
			style_function = lambda feature: style_mdl(feature),
		).add_to(m)
	elif len(slc_mdl) == 4:
		cursor.execute("""CREATE OR REPLACE VIEW rota_modal_selec AS SELECT rotas_filtradas.* FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' 
		UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1], slc_mdl[2], slc_mdl[3]))
		cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal) As l)) As properties FROM rota_modal_selec As lg   ) As f )  As fc;""")
		json_mdl = json.dumps(cursor.fetchall())
		tbl = pd.read_sql_query("""SELECT rotas_filtradas.id_rota as id, modais.nm_modal as modal, rotas_filtradas.dia as data FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1], slc_mdl[2], slc_mdl[3]), conn)
		conn.commit()
		if show_tbls:
			tbl
		lyr_mdl = folium.GeoJson(
			json_mdl[2:len(json_mdl)-2],
			name = 'Layer Modais',
			style_function = lambda feature: style_mdl(feature),
		).add_to(m)
	else: 
		cursor.execute("""CREATE OR REPLACE VIEW rota_modal_selec AS SELECT rotas_filtradas.* FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' 
		UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.* FROM rotas_filtradas, modais 
		WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1], slc_mdl[2], slc_mdl[3], slc_mdl[4]))
		cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal) As l)) As properties FROM rota_modal_selec As lg ) As f )  As fc;""")
		json_mdl = json.dumps(cursor.fetchall())
		tbl = pd.read_sql_query("""SELECT rotas_filtradas.id_rota as id, modais.nm_modal as modal, rotas_filtradas.dia as data FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s' UNION SELECT rotas_filtradas.id_rota, modais.nm_modal, rotas_filtradas.dia FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %(slc_mdl[0], slc_mdl[1], slc_mdl[2], slc_mdl[3], slc_mdl[4]), conn)
		conn.commit()
		if show_tbls:
			tbl
		lyr_mdl = folium.GeoJson(
			json_mdl[2:len(json_mdl)-2],
			name = 'Layer Modais',
			style_function = lambda feature: style_mdl(feature),
		).add_to(m)

# Função que executa as consultas com relação ao tema (individual)
def func_tm(slc_tm):
	# --- TEMA --- #
	if slc_tm == 'Nenhum':
		pass
	elif slc_tm == 'Ruído Sonoro':
		with st.spinner('Consultando o banco de dados, só um instantinho...'):
			# tema: DB - Todas as rotas/Todos os usuarios
			# LINHA
			cursor.execute("""CREATE OR REPLACE VIEW osm_db_rota AS SELECT row_number() OVER (PARTITION BY true) as id, osm_db.osm_id, ponto_rua.id_rota, osm_db.geom, osm_db.db_medio FROM osm_db, ponto_rua WHERE ponto_rua.osm_id = osm_db.gid;""")
			cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT id, db_medio) As l)) As properties FROM osm_db_rota As lg ) As f )  As fc;""")
			json_line_tm = json.dumps(cursor.fetchall())
			# data_chart = pd.read_sql_query("SELECT id_rota, sum(db_medio) FROM osm_db_rota GROUP BY id_rota", conn)
			conn.commit()
			# st.bar_chart(data_chart)
			# --- Para cada ponto carrega um marker = demora muito --- #
			lyr_line_tm = folium.GeoJson(
				json_line_tm[2:len(json_line_tm)-2],
				name = 'Tema ruído Linha',
				style_function = lambda feature: style_tm_db(feature),
				).add_to(m)
	else:
		with st.spinner('Consultando o banco de dados, só um instantinho...'):
			# tema: VELOCIDADE - Todas as rotas/Todos os usuarios
			# LINHA
			cursor.execute("""CREATE OR REPLACE VIEW osm_veloc_rota AS SELECT row_number() OVER (PARTITION BY true) as id, osm_veloc.osm_id, ponto_rua_veloc.id_rota, osm_veloc.geom, osm_veloc.veloc_medio FROM osm_veloc, ponto_rua_veloc WHERE ponto_rua_veloc.osm_id = osm_veloc.gid;""")
			cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT id, veloc_medio) As l)) As properties FROM osm_veloc_rota As lg ) As f )  As fc;""")
			json_line_tm = json.dumps(cursor.fetchall())
			# data_chart = pd.read_sql_query("SELECT id_rota, sum(veloc_medio) FROM osm_veloc_rota GROUP BY id_rota", conn)
			conn.commit()
			# st.info('Velocidade média por rotas')
			# st.bar_chart(data_chart)
			lyr_line_tm = folium.GeoJson(
				json_line_tm[2:len(json_line_tm)-2],
				name = 'Tema ruído Linha',
				style_function = lambda feature: style_tm_veloc(feature),
				).add_to(m)

# Função que executa as consultas COMBINADAS entre modais e tema
def func_mdl_tm(slc_mdl, slc_tm):
	if slc_tm == 'Ruído Sonoro':
		with st.spinner('Consultando o banco de dados, só um instantinho...'):
			cursor.execute("""CREATE OR REPLACE VIEW osm_db_modal AS SELECT osm_db_rota.*, modais.modal_id FROM osm_db_rota, rota_modal, modais WHERE osm_db_rota.id_rota = rota_modal.id_rota AND rota_modal.modal = modais.modal_id AND modais.nm_modal = '%s';""" %slc_mdl)
			cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT id, db_medio) As l)) As properties FROM osm_db_modal As lg ) As f )  As fc;""")
			json_line_cbn = json.dumps(cursor.fetchall())
			conn.commit()
			lyr_line_cbn = folium.GeoJson(
				json_line_cbn[2:len(json_line_cbn)-2],
				name = 'Modais por tema ruído sonoro',
				style_function = lambda feature: style_tm_db(feature),
				).add_to(m)
	else:
		with st.spinner('Consultando o banco de dados, só um instantinho...'):
			cursor.execute("""CREATE OR REPLACE VIEW osm_veloc_modal AS SELECT osm_veloc_rota.*, modais.modal_id FROM osm_veloc_rota, rota_modal, modais WHERE osm_veloc_rota.id_rota = rota_modal.id_rota AND rota_modal.modal = modais.modal_id AND modais.nm_modal = '%s';""" %slc_mdl)
			cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT id, veloc_medio) As l)) As properties FROM osm_veloc_modal As lg ) As f )  As fc;""")
			json_line_cbn = json.dumps(cursor.fetchall())
			conn.commit()
			lyr_line_cbn = folium.GeoJson(
				json_line_cbn[2:len(json_line_cbn)-2],
				name = 'Modais por tema velocidade',
				style_function = lambda feature: style_tm_veloc(feature),
				).add_to(m)

# Função que executa as consultas por data e modal
def func_date_mdl(date_time):
	cursor.execute("""CREATE OR REPLACE VIEW rotas_filtradas_data_selec AS SELECT * FROM rotas_filtradas_data WHERE date = '%s'""" %date_time)
	cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal, date) As l)) As properties FROM rotas_filtradas_data_selec As lg ) As f )  As fc;""")
	json_date_list = json.dumps(cursor.fetchall())
	conn.commit()
	json_date = json_date_list[2:len(json_date_list)-2]
	if json.loads(json_date)['features'] is None:
		st.warning('Não há dados registrados nesta data')
	else:
		lyr_date = folium.GeoJson(
			json_date,
			name = 'Modal por data',
			style_function = lambda feature: style_mdl(feature),
			).add_to(m)

# Função que executa as consultas por data e tema (db)
def func_date_tm_db(date_time):
	cursor.execute("""CREATE OR REPLACE VIEW osm_db_data_selec AS SELECT osm_db_rota.*, rotas_filtradas_data.date FROM osm_db_rota, rotas_filtradas_data WHERE osm_db_rota.id_rota = rotas_filtradas_data.id_rota AND rotas_filtradas_data.date = '%s' """ %date_time)
	cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT id, db_medio, date) As l)) As properties FROM osm_db_data_selec As lg ) As f )  As fc;""")
	json_date_list = json.dumps(cursor.fetchall())
	conn.commit()
	json_date = json_date_list[2:len(json_date_list)-2]
	if json.loads(json_date)['features'] is None:
		pass
	else:
		lyr_date = folium.GeoJson(
			json_date,
			name = 'Tema ruído sonoro por data',
			style_function = lambda feature: style_tm_db(feature),
			show = False,
			).add_to(m)

# Função que executa as consultas por data e tema (veloc)
def func_date_tm_veloc(date_time):
	cursor.execute("""CREATE OR REPLACE VIEW osm_veloc_data_selec AS SELECT osm_veloc_rota.*, rotas_filtradas_data.date, rotas_filtradas_data.time FROM osm_veloc_rota, rotas_filtradas_data WHERE osm_veloc_rota.id_rota = rotas_filtradas_data.id_rota AND rotas_filtradas_data.date = '%s' """ %date_time)
	cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT id, veloc_medio, date, time) As l)) As properties FROM osm_veloc_data_selec As lg ) As f )  As fc;""")
	json_date_list = json.dumps(cursor.fetchall())
	conn.commit()
	json_date = json_date_list[2:len(json_date_list)-2]
	if json.loads(json_date)['features'] is None:
		pass
	else:
		lyr_date = folium.GeoJson(
			json_date,
			name = 'Tema velocidade por data',
			style_function = lambda feature: style_tm_veloc(feature),
			show = False,
			).add_to(m)

# --- CANVAS --- #
st.title('SmartMobility')
st.header('Solução de Geoinformação para estudos em Mobilidade Urbana')

m = folium.Map(location = [-25.45,-49.26],
               zoom_start = 13,
               tiles = 'Cartodb Positron')

# --- SIDEBAR --- #
st.sidebar.title('Consultas espaciais')

# Checkbox para mostrar dados tabelares
show_tbls = st.sidebar.checkbox('Mostrar dados tabelares')

# Escolha do tipo de consulta espacial que sera feita nos dados
cslt_radio = st.sidebar.radio(
	'Os dados podem ser consultados de forma:',
	('Individual', 'Combinada', 'Por data'))

# Condicao do tipo de consulta
if cslt_radio == 'Individual':
	st.markdown('Consultas espaciais _individuais_ dos dados classificados por **modais ou temas**')
	# Escolha dos modais
	slc_mdl = st.sidebar.multiselect(
		'Modais',
		lista_modal())

	# Escolha dos tema dos mapas
	slc_tm = st.sidebar.selectbox('Tema', ('Nenhum', 'Ruído Sonoro', 'Velocidade'))
	
	# Executando as funções com os parâmetros escolhidos acima
	func_mdl(slc_mdl)
	func_tm(slc_tm)
elif cslt_radio == 'Combinada':
	st.markdown('Consultas espaciais _combinadas_ entre os dados classificados por **modais e temas**')
	# Escolha dos modais
	slc_mdl = st.sidebar.selectbox('Modais', lista_modal())

	# Escolha dos tema dos mapas
	slc_tm = st.sidebar.selectbox('Tema', ('Ruído Sonoro', 'Velocidade'))
	
	# Executando as funções com os parâmetros escolhidos acima
	func_mdl_tm(slc_mdl, slc_tm)
else:
	st.markdown('Consulta espaciais filtrados por _data_')
	date_time = st.sidebar.date_input('Filtrar os dados por data', datetime.datetime(2018, 5, 1), datetime.datetime(2018, 5, 1), datetime.datetime(2018,8,1))
	with st.spinner('Consultando o banco de dados, só um instantinho...'):
		func_date_mdl(date_time)
		func_date_tm_db(date_time)
		func_date_tm_veloc(date_time)

folium.LayerControl(
	collapsed = False,
).add_to(m)
folium_static(m)

cursor.close()
conn.close()

# Slider que duplo
# st.sidebar.slider("Teste", 0, 25, [10, 20])
# Consulta media veloc por hora
# tbl = pd.read_sql_query("SELECT time AS Hora, AVG(veloc_medio) AS Velocidade_Media FROM osm_veloc_data_selec WHERE date = '%s' GROUP BY time """ %date_time, conn)
# Tentativa
# cursor.execute("""CREATE OR REPLACE VIEW text_veloc_medio AS SELECT AVG(veloc_medio) FROM osm_veloc_modal, modais WHERE osm_veloc_modal.modal_id = modais.modal_id AND modais.nm_modal = '%s' GROUP BY nm_modal""" %slc_mdl)
# query = cursor.fetchall()
# st.success('O ruído sonoro médio do modal %s em decibéis é %s' %(slc_mdl, query[0][0]))