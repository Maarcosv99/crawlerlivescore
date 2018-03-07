import requests
from bs4 import BeautifulSoup
from administracao.models import Analise, Prognostico
from aovivo.models import JogoAnaliseAoVivo, JogoAoVivo

#CRAWLER DO PLACAR DE FUTEBOL
def autenticacaoPlacar():
	url = 'https://www.placardefutebol.com.br/jogos-de-hoje'
	proxies = {'http':'107.170.42.158:80'}
	r = requests.get(url)
	soup = BeautifulSoup(r.text, 'lxml')
	return soup

def jogos():
	soup = autenticacaoPlacar()
	url = 'https://www.placardefutebol.com.br'
	campeonatos = soup.find('div', {'id':'livescore'}).find_all('div', {'class':'container content'})
	todos_jogos = []
	for campeonato in campeonatos:
		jogos = campeonato.find_all('a')
		for jogo in jogos:
			jogo = dados_jogo(jogo)
			if jogo['time_casa'] and jogo['time_fora']:
				if jogo['status'] == 'AO VIVO' or jogo['status'].find('MIN') > 0:
					todos_jogos.append(jogo)
	return todos_jogos

def dados_jogo(jogo):
	url = 'https://www.placardefutebol.com.br'
	jogo_link = '{0}{1}'.format(url, jogo['href'])
	jogo_status = jogo.find(class_='status-name').string
	jogo_time_casa = jogo.find(class_='team_link').string
	try:
		jogo_time_casa_gols = jogo.find(class_='match-score').find(class_='badge').string
	except AttributeError:
		jogo_time_casa_gols = '0'
	jogo_time_fora = jogo.find_all(class_='team_link')[1].string
	try:
		jogo_time_fora_gols = jogo.find_all(class_='match-score')[1].find(class_='badge').string
	except AttributeError:
		jogo_time_fora_gols = '0'
	return {'link':jogo_link,'status':jogo_status,'time_casa': jogo_time_casa,'time_casa_gol': jogo_time_casa_gols,'time_fora': jogo_time_fora,'time_fora_gol': jogo_time_fora_gols}

def procurar_jogo(todos_jogos, time_casa, time_fora):
	for jogo in todos_jogos:
		if jogo['time_casa'].find(time_casa) >= 0 and jogo['time_fora'].find(time_fora) >= 0:
			return jogo
	return False

def status_gol(jogo):
	link = jogo['link']
	r = requests.get(link)
	soup = BeautifulSoup(r.text, 'lxml')
	eventos_casa = soup.find_all('div', {'class':'match-card-events-home-team'})
	eventos_fora = soup.find_all('div', {'class':'match-card-events-away-team'})
	gols_casa_ft = 0
	gols_casa_ht = 0
	for evento_casa in eventos_casa:
		try:
			gols_casa = evento_casa.find_all('i', {'class':'fa fa-futbol-o'})
			for gol_casa in gols_casa:
				gols_casa_ft += 1
				tempo_do_gol = gol_casa.next_sibling
				tempo_do_gol = int(tempo_do_gol.replace(" - ","").replace("'", ""))
				if tempo_do_gol <= 45:
					gols_casa_ht += 1
		except:
			gols_casa = 0

	gols_fora_ft = 0
	gols_fora_ht = 0
	for evento_fora in eventos_fora:
		try:
			gols_fora = evento_fora.find_all('i', {'class':'fa fa-futbol-o'})
			for gol_fora in gols_fora:
				gols_fora_ft += 1
				tempo_do_gol = gol_fora.previous_sibling
				tempo_do_gol = int(tempo_do_gol[:1])
				if tempo_do_gol <= 45:
					gols_fora_ht += 1
		except:
			gols_fora = 0			

	return {'CasaHT':gols_casa_ht, 'CasaFT': gols_casa_ft, 'ForaHT': gols_fora_ht, 'ForaFT': gols_fora_ft}

def jogoAnaliseAoVivo(todos_jogos):
	ultimaAnalise = Analise.objects.all().order_by('-id')[0]
	prognosticos = Prognostico.objects.all().filter(analise=ultimaAnalise).order_by('-id')
	tamanho_lista = len(prognosticos)
	index = 0
	for jogo in prognosticos:
		index += 1
		response = procurar_jogo(todos_jogos, jogo.time_casa, jogo.time_fora)
		if response:
			if type(response) is dict:
				try:
					instancia = JogoAnaliseAoVivo.objects.all().order_by('-id')[0]
				except:
					instancia = JogoAnaliseAoVivo(
						time_casa=response['time_casa'],
						time_casa_gol=response['time_casa_gol'],
						time_fora=response['time_fora'],
						time_fora_gol=response['time_fora_gol'],
						tip=jogo.entrada)
					instancia.save()
					break
					return True
				instancia.time_casa=response['time_casa']
				instancia.time_casa_gol=response['time_casa_gol']
				instancia.time_fora=response['time_fora']
				instancia.time_fora_gol=response['time_fora_gol']
				instancia.tip=jogo.entrada
				instancia.save()
				break
				return True
		elif index == (tamanho_lista - 1):
			instancia = JogoAnaliseAoVivo.objects.all().order_by('-id')[0]
			instancia.time_casa=None
			instancia.time_casa_gol=None
			instancia.time_fora=None
			instancia.time_fora_gol=None
			instancia.tip=None
			instancia.save()
			return True



def jogoAoVivo(todos_jogos):
	jogo = todos_jogos[0]
	if not jogo:
		instancia = JogoAoVivo.objects.all().order_by('-id')[0]
		instancia.time_casa=None
		instancia.time_casa_gol=None
		instancia.time_fora=None
		instancia.time_fora_gol=None
		instancia.save()
		return True
	else:
		try:
			instancia = JogoAoVivo.objects.all().order_by('-id')[0]
		except:
			instancia = JogoAoVivo(
				time_casa=jogo['time_casa'],
				time_casa_gol=jogo['time_casa_gol'],
				time_fora=jogo['time_fora'],
				time_fora_gol=jogo['time_fora_gol'])
			instancia.save()
			return True
		instancia.time_casa=jogo['time_casa']
		instancia.time_casa_gol=jogo['time_casa_gol']
		instancia.time_fora=jogo['time_fora']
		instancia.time_fora_gol=jogo['time_fora_gol']
		instancia.save()
		return True
