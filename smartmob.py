import streamlit as st
import pandas as pd
import numpy as np
import psycopg2
import streamlit as st
from streamlit_folium import folium_static
import folium
import json
import time

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

# --- SIDEBAR --- #
st.sidebar.title('Consultas espaciais')

# Escolha dos modais
slc_mdl = st.sidebar.multiselect(
    'Modais',
    lista_modal())

# Escolha dos tema dos mapas
slc_tm = st.sidebar.selectbox('Tema', ('Nenhum', 'Ruído Sonoro', 'Velocidade'))

# Checkbox para mostrar dados tabelares
show_tbls = st.sidebar.checkbox('Mostrar dados tabelares')

# --- CANVAS --- #
st.title('SmartMobility')
st.markdown('## Solução de Geoinformação para estudos em Mobilidade Urbana')

m = folium.Map(location = [-25.45,-49.26],
               zoom_start = 13,
               tiles = 'Cartodb Positron')

# --- Consultas no banco --- #
# --- MODAIS --- #
if len(slc_mdl) == 0:
	pass
elif len(slc_mdl) == 1:
	cursor.execute("""CREATE OR REPLACE VIEW rota_modal_selec AS SELECT rotas_filtradas.* FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %slc_mdl[0])
	cursor.execute("""SELECT row_to_json(fc) FROM ( SELECT 'FeatureCollection' As type, array_to_json(array_agg(f)) As features FROM (SELECT 'Feature' As type, ST_AsGeoJSON(lg.geom)::json As geometry, row_to_json((SELECT l FROM (SELECT gid, modal) As l)) As properties FROM rota_modal_selec As lg   ) As f )  As fc;""")
	json_mdl = json.dumps(cursor.fetchall())
	# Tabela com informacoes dos dados do mapa
	tbl = pd.read_sql_query("SELECT rotas_filtradas.id_rota as id, rotas_filtradas.dia as data FROM rotas_filtradas, modais WHERE rotas_filtradas.modal = modais.modal_id AND modais.nm_modal = '%s'""" %slc_mdl[0], conn)
	# st.json(json_mdl[2:len(json_mdl)-2])
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

folium.LayerControl().add_to(m)
folium_static(m)

cursor.close()
conn.close()
