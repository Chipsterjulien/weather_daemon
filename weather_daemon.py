#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#jeu. 08 nov. 2012

# Depend of python-yaml, python-requests

import urllib.request
import json, sys, os, time, copy, yaml, requests, logging




######
# Classe
############

class Condition:
	def __init__(self, name):
		self.name = name




######
# Début du programme principal
############

error_file        = "/var/log/weather_daemon/error.log"
conf_file         = "/etc/weather_daemon.conf"
icons_weather_dir = "/usr/share/weather_daemon/icons"
logging.basicConfig(filename=error_file, format='%(asctime)s %(message)s', level=logging.WARNING)

# On découpe les fichiers pour obtenir le path et le fichier
(path, f) = os.path.split(error_file)
# On vérifie les droits d'écriture dans le fichier log
if not os.access(path, os.W_OK):
	print("You don't have the writing permissions on  \"" + path + "\"\n", file=sys.stderr)
	sys.exit(2)

# Pareil que précédemment mais sur le fichier de configuration
(path, f) = os.path.split(conf_file)
if not os.access(path, os.R_OK):
	logging.critical("You don't have the reading permission on \"" + conf_file + "\"\n")
	sys.exit(2)

if not os.path.isfile(conf_file):
	logging.critical("The file \"" + conf_file + "\" doesn't exist !\n")
	sys.exit(2)

# On teste les droits de lecture sur le fichier de configuration
if not os.access(conf_file, os.R_OK):
	logging.critical("You don't have the reading permissions on \"" + conf_file + "\"\n")
	sys.exit(2)


# Chargement du fichier de configuration
source = open(conf_file, 'r')
data   = yaml.load(source.read())
source.close()

# On vérifie que l'emplacement du fichier pour enregistrer les données existe
(path, f) = os.path.split(data['file'])
if path == "":
	path = os.path.expanduser('~')
	data['file'] = os.path.join(path, f)
# On vérifie qu'on a les droits d'écritures
if not os.access(path, os.W_OK):
	logging.critical("You don't have the writing permissions on \"" + data['file'] + "\"\n")
	sys.exit(2)

# On vérifie qu'on a les droits de lecture sur les icons du temps
if not os.access(icons_weather_dir, os.R_OK):
	logging.critical("You don't have the reading permissions on \"" + icons_weather_dir + "\"\n")
	sys.exit(2)


# On vérifie que le temps donné dans le fichier de configuration est bien un entier > 0
try :
	s = int(data['sleep'])
	if s <= 0:
		logging.critical("\"" + data['sleep'] + "\" is not greater or equal to 0 !\n")
		sys.exit(2)
except ValueError:
	logging.critical("\"" + data['sleep'] + "\" is not an integer !\n")
	sys.exit(2)


# On démarre la boucle infinie
while 1:
	page_json = str()
#	try:
#		page_json = urllib.request.urlopen(data['url']) # On récupère la page json
#	except urllib.error.URLError as e:                # Si on n'y arrive pas on récupère l'exception
#		logging.warning("Unable to download " + data['url'] + "\n") # On affiche l'erreur avec l'heure du souci
#		time.sleep(20)                                  # On attend 20s avant de recommencer
#		continue                                        # On passe à la boucle souvante
	try:
		page_json = requests.get(data['url'])
	except requests.exceptions.ConnectionError:
		time.sleep(10)
		os.execl('/usr/bin/weather_daemon', 'weather_daemon')

	if page_json.status_code != requests.codes.ok:
		logging.critical(data['url'] + " isn't a valid url !")
		sys.exit(2)

	reading = page_json.content.decode('utf-8', 'ignore')
	if "keynotfound" in reading:                   # On vérifie que le serveur ne nous renvoie pas une erreur liée à clef fausse
		logging.critical("The URL key is wrong !\n") # On affiche l'erreur avec l'heure du souci
		sys.exit(2)

	parsed_json = json.loads(reading)                                            # On charge le code json
	page_json.close()                                                            # On ferme la page


	# Définition des variables
	now   = Condition('now')
	today = tomorrow = after_tomorrow = latest = tmp = Condition('nothing')

	
	now.city = parsed_json['location']['city']                                                                      # On récupère la ville
	now.hour = time.strftime('%H:%M', time.localtime(int(parsed_json['current_observation']['observation_epoch']))) # On récupère l'heure actuelle
	now.current_temperature = parsed_json['current_observation']['temp_c']                                          # On récupère la température actuelle en °C
	now.current_weather = parsed_json['current_observation']['weather']                                             # On récupère le temps actuel
	now.humidity = parsed_json['current_observation']['relative_humidity']                                          # On récupère l'humidité
	now.wind_kph = parsed_json['current_observation']['wind_kph']                                                   # On récupère la vitesse du vent
	now.wind_dir = parsed_json['current_observation']['wind_dir']                                                   # On récupère l'orientation du vent
	now.wind_degrees = parsed_json['current_observation']['wind_degrees']                                           # On récupère l'orientation du vent en °C
	now.pressure_mb = parsed_json['current_observation']['pressure_mb']                                             # On récupère la pression
	now.dewpoint_c = parsed_json['current_observation']['dewpoint_c']                                               # On récupère le point de rosée
	now.feelslike_c = parsed_json['current_observation']['feelslike_c']                                             # On récupère la température ressentie
	now.visibility = parsed_json['current_observation']['visibility_km']                                            # On récupère la visibilité
	now.UV = parsed_json['current_observation']['UV']                                                               # On récupère l'indice UV
	now.icon = parsed_json['current_observation']['icon']                                                           # On récupère l'icône
	now.precip = parsed_json['current_observation']['precip_today_metric']                                          # On récupère la hauteur de la pluie
	now.update_time = " ".join(parsed_json['current_observation']['observation_time'].split(","))                   # On récupère l'heure de la dernière mise à jour. On en profite pour
	                                                                                                                # supprimer une , inutile


	# On récupère les prévisions à 4 jours
	forecast = parsed_json['forecast']['simpleforecast']['forecastday']
	for i in forecast:
		tmp.temp_max      = i['high']['celsius']       # Température max
		tmp.temp_min      = i['low']['celsius']        # Température min
		tmp.conditions    = i['conditions']            # Conditions météo
		tmp.icon          = i['icon']                  # Icône du temps
		tmp.wind_max      = i['maxwind']['kph']        # Vitesse du vent max
		tmp.wind_max_dir  = i['maxwind']['dir']        # Direction du vent
		tmp.wind_max_deg  = i['maxwind']['degrees']    # Direction du vent en °
		tmp.wind_ave      = i['avewind']['kph']        # Vitesse moyenne du vent
		tmp.wind_ave_dir  = i['avewind']['dir']        # Direction moyenne du vent
		tmp.wind_ave_deg  = i['avewind']['degrees']    # Direction moyenne du vent en °
		tmp.humidity_ave  = i['avehumidity']           # Humidité moyenne
		tmp.humidity_max  = i['maxhumidity']           # Humidité max
		tmp.humidity_min  = i['minhumidity']           # Humidité min
		tmp.day           = i['date']['day']           # Numéro du jour
		tmp.month         = i['date']['month']         # Numéro du mois
		tmp.pop           = i['pop']                   # Pourcentage de chance que ça arrive
		tmp.qpf_allday    = i['qpf_allday']['mm']      # Précipitations totales en mm
		tmp.snow_day      = i['snow_day']['cm']        # Neige totale en cm
		tmp.weekday_short = i['date']['weekday_short'] # Nom du jour au format court

		# On donne un nom aux infos récupérer
		if i['period'] == 1:
			tmp.name = 'today'
			today = copy.copy(tmp)
		elif i['period'] == 2:
			tmp.name = 'tomorrow'
			tomorrow = copy.copy(tmp)
		elif i['period'] == 3:
			tmp.name = 'after'
			after_tomorrow = copy.copy(tmp)
		elif i['period'] == 4:
			tmp.name = 'latest'
			latest = copy.copy(tmp)
		else:
			logging.warning("Unknown day : \"period = " + i['period'] + "\"\n")


	# On sauvegarde les infos dans l'emplacement indiqué par data['file']
	with open(data['file'], 'w') as c:
		c.write("Condition = " + now.current_weather + "\n")
		c.write("City = " + now.city + "\n")
		c.write("Hour = " + now.hour + "\n")
		c.write("Temperature = " + str(now.current_temperature) + "\n")
		c.write("Feelslike_c = " + now.feelslike_c + "\n")
		c.write("Humidity = " + now.humidity + "\n")
		c.write("Wind_speed = " + str(now.wind_kph) + "\n")
		c.write("Wind_dir = " + now.wind_dir + "\n")
		c.write("Wind_degrees = " + str(now.wind_degrees) + "\n")
		c.write("Pressure = " + now.pressure_mb + "\n")
		c.write("Dewpoint = " + str(now.dewpoint_c) + "\n")
		c.write("Visibility = " + now.visibility + "\n")
		c.write("UV = " + now.UV + "\n")
		c.write("Precipitation = " + now.precip + "\n")
		c.write("Icon = " + now.icon + "\n")
		c.write("Update_time = " + now.update_time + "\n")

		# On gère la gestion du vent sur une rose avec la partie suivante en fonction de l'orientation en °
		tmp = "Wind_conky = "
		if now.wind_kph == 0:
			tmp += '%'

		elif now.wind_kph <= 30:
			if now.wind_degrees < 11.25:
				tmp += '1'
			elif now.wind_degrees < 33.75:
				tmp += '2'
			elif now.wind_degrees < 56.25:
				tmp += '3'
			elif now.wind_degrees < 78.75:
				tmp += '4'
			elif now.wind_degrees < 101.25:
				tmp += '5'
			elif now.wind_degrees < 123.75:
				tmp += '6'
			elif now.wind_degrees < 146.25:
				tmp += '7'
			elif now.wind_degrees < 168.75:
				tmp += '8'
			elif now.wind_degrees < 191.25:
				tmp += '9'
			elif now.wind_degrees < 213.75:
				tmp += ':'
			elif now.wind_degrees < 236.25:
				tmp += ';'
			elif now.wind_degrees < 258.75:
				tmp += '<'
			elif now.wind_degrees < 281.25:
				tmp += '='
			elif now.wind_degrees < 303.75:
				tmp += '>'
			elif now.wind_degrees < 326.25:
				tmp += '?'
			elif now.wind_degrees < 348.75:
				tmp += '@'
			elif now.wind_degrees > 348.75:
				tmp += '1'

		elif now.wind_kph <= 60:
			if now.wind_degrees < 11.25:
				tmp += 'A'
			elif now.wind_degrees < 33.75:
				tmp += 'B'
			elif now.wind_degrees < 56.25:
				tmp += 'C'
			elif now.wind_degrees < 78.75:
				tmp += 'D'
			elif now.wind_degrees < 101.25:
				tmp += 'E'
			elif now.wind_degrees < 123.75:
				tmp += 'F'
			elif now.wind_degrees < 146.25:
				tmp += 'G'
			elif now.wind_degrees < 168.75:
				tmp += 'H'
			elif now.wind_degrees < 191.25:
				tmp += 'I'
			elif now.wind_degrees < 213.75:
				tmp += 'J'
			elif now.wind_degrees < 236.25:
				tmp += 'K'
			elif now.wind_degrees < 258.75:
				tmp += 'L'
			elif now.wind_degrees < 281.25:
				tmp += 'M'
			elif now.wind_degrees < 303.75:
				tmp += 'N'
			elif now.wind_degrees < 326.25:
				tmp += 'O'
			elif now.wind_degrees < 348.75:
				tmp += 'P'
			elif now.wind_degrees > 348.75:
				tmp += 'A'

		elif now.wind_kph > 60:
			if now.wind_degrees < 11.25:
				tmp += 'a'
			elif now.wind_degrees < 33.75:
				tmp += 'b'
			elif now.wind_degrees < 56.25:
				tmp += 'c'
			elif now.wind_degrees < 78.75:
				tmp += 'd'
			elif now.wind_degrees < 101.25:
				tmp += 'e'
			elif now.wind_degrees < 123.75:
				tmp += 'f'
			elif now.wind_degrees < 146.25:
				tmp += 'g'
			elif now.wind_degrees < 168.75:
				tmp += 'h'
			elif now.wind_degrees < 191.25:
				tmp += 'i'
			elif now.wind_degrees < 213.75:
				tmp += 'j'
			elif now.wind_degrees < 236.25:
				tmp += 'k'
			elif now.wind_degrees < 258.75:
				tmp += 'l'
			elif now.wind_degrees < 281.25:
				tmp += 'm'
			elif now.wind_degrees < 303.75:
				tmp += 'n'
			elif now.wind_degrees < 326.25:
				tmp += 'o'
			elif now.wind_degrees < 348.75:
				tmp += 'p'
			elif now.wind_degrees > 348.75:
				tmp += 'a'
		else:
			tmp += "-"

		c.write(tmp + "\n")

		# On gère la gestion des icônes des conditions atmosphériques en fonction de l'heure
		(h, m) = now.hour.split(":")
		h = int(h)
		# Si l'heure est comprise entre 6h du matin et du soir, on affiche les icônes jour
		if h >= 6 and h <= 18:
			c.write("Now_conky_icon = ${image " + os.path.join(icons_weather_dir, "daytime", now.icon) + ".png }\n")
		else:
			c.write("Now_conky_icon = ${image " + os.path.join(icons_weather_dir, "nighttime", now.icon) + ".png }\n")


		for var in [today, tomorrow, after_tomorrow, latest]:
			c.write(var.name + "_temp_max = " + var.temp_max + "\n")
			c.write(var.name + "_temp_min = " + var.temp_min + "\n")
			c.write(var.name + "_conditions = " + var.conditions + "\n")
			c.write(var.name + "_icon = " + var.icon +"\n")
			c.write(var.name + "_wind_max = " + str(var.wind_max) + "\n")
			c.write(var.name + "_wind_max_dir = " + var.wind_max_dir + "\n")
			c.write(var.name + "_wind_max_deg = " + str(var.wind_max_deg) + "\n")
			c.write(var.name + "_wind_ave = " + str(var.wind_ave) + "\n")
			c.write(var.name + "_wind_ave_dir = " + var.wind_ave_dir + "\n")
			c.write(var.name + "_wind_ave_deg = " + str(var.wind_ave_deg) + "\n")
			c.write(var.name + "_humidity_max = " + str(var.humidity_max) + "\n")
			c.write(var.name + "_humidity_min = " + str(var.humidity_min) + "\n")
			c.write(var.name + "_humidity_ave = " + str(var.humidity_ave) + "\n")
			c.write(var.name + "_pop = " + str(var.pop) + "\n")
			c.write(var.name + "_qpf_allday = " + str(var.qpf_allday) + "\n")
			c.write(var.name + "_day = " + str(var.day) + "\n")
			c.write(var.name + "_month = " + str(var.month) + "\n")
			c.write(var.name + "_weekday_short = " + str(var.weekday_short) + "\n")

			c.write(var.name + "_conky_icon = ${image " + os.path.join(icons_weather_dir, "daytime", var.icon) + ".png }\n")
	
	the_time = time.time()
	loop = True
	while loop:
		# On récupère l'heure
		time_tmp = time.time()
		# Si on a dormi trop longtemps, on quitte la boucle
		if the_time + data['sleep'] < time_tmp:
			loop = False

		# Sinon on va s'endormir et se réveiller régulièrement
		else:
			# On calcule le temps qu'il nous reste à dormir
			rest = (the_time + data['sleep']) - time_tmp
			# S'il est inférieur à 2s par besoin de se rendormir inutilement
			if rest < 2:
				loop = False
			# S'il est inférieur à 120s, on se rendort du temps qu'il reste
			elif rest < 120:
				time.sleep(rest)
			# Autrement, on s'endort pendant 120s
			else:
				time.sleep(120)
