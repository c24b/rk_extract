#RK challenge

##Contextes
Rakuten.py est un mini script qui consitute
une proto-api d'interrogation et d'extraction de données
issues de la plateforme rakuten.co.jp
ce script propose plusieurs méthodes d'interrogation et d'extraction 
des données. 
Le site en question ne pose pas de problème particulier
- dans son accès: tout est disponible sans avoir besoin 
d'émuler un navigateur (pas besoin d'un selenium donc)
- dans sa recherche:
les parametres de recherche de produits sont tous disponibles dans l'url
et procèdent d'une nomenclature bien détaillée faciloe à reproduire

- dans ses pages:
les tags utilisés sont suffisamments spécifiques pour accéder à une 
information qualifiée

## Implémentation
Nous avons donc simplement utilisé requests et beautifulsoup4 (parser 
au dessus de lxml) ainsi que pour des raisons de temps de téléchargement
une petite librairie qui permet de faire des requetes de manière non bloquante
pour éviter les effets de ralentissement du script en fonction 
de la disponibilité de la page .


Face au travail qui a été demandé, la methode collect_luxury fonctionne 
comme un raccourci même si elle n'est pas très satsifaisante: en effet
les différentes pages n'ont pas la meme arborescence ce qui impliquait 
des gestions d'exception à 5 ou 6 niveaux que j'ai remplacé par un filtre 
textuel pour simplifier l'accès au niveau de pages suivants.

## TO DO
Pour des raisons de temps, les insertions en base de données
sont minimales et mal structurées (MongoDb permet en effet de 
ne pas fortement structurer ses contenus ) 
Evidemment  il faudrait stocker les résultats des extractions afin de ne pas le refaire 
à chaque recherche. Une base de données plus formelle et structurée proprement 
permettrait à la fois de donner une dimension historique d'analyse
et de releguer les traitements et matching non plus au niveau du script mais 
au niveau de la Base de données ne mettant à jour que ce qui a besoin de l'être.

Il faudrait évidemment proposer un moyen d'agréger les données dans le temps 
soit en cron par jour ou par semaine (le plus rapide) soit avec Celery 
ou un AppScheduler pour une gestion 
plus fine et intégrée des tâches et une mise à jour de la BDD sur laquelle
l'interface s'appuiera pour la présentation de ses résulats.

* Données pour l'interface

Le script propose de fait l'accès à trois types d'informations
- les informations liées au résultats de recherche et contextuels
	- combien de résultats pour cette recherche
	- combien de pages pour cette recherche

- des informations comparatives en fonction du scope de la recherche 
ou du niveau de détail désiré
	- combien de résultats dans les autres catégories 
	- combien de résultats pour les autres marques 

- l'intégralité des informations disponible sur les produits extraits
(si renseigné)
	```
	{"photo_src": #l'adresse media de la photo pour pouvoir la télécharger,
	"price": #le prix,
	"page_url":#la page du produit avec les comparateurs,
	"review_nb": #le nombre d'avis,
	"review_page":# la page de l'avis détaillé,
	"shop_name":# le nom du vendeur,
	"shop_url": #la page du vendeur (externe/interne),
	"insurance":False #si le produit est assuré,
	"paiement_mode": # le type de paiemennt accepté,
	"product_info":# la page produit,
	"url": #l'url exacte de recherche,
	"id": #l'identiant du produit,
	"title": #titre de l'annonce
	"description": # description textuelle du produit
	}
	```
Dans une interface donc on se chargerait de donner deux niveaux d'accès
résultats d'une recherche ou résultats produits + résultats dans une fenetre 
temporelle

Evidemment dans un cas de détection de fraude ou de contrefacon:
il serait le bienvenue de caractériser les facteurs de risques pour 
emmettre un score de confiance
- pas d'assurance
- paiement uniquement par carte
- pas d'avis ou avis négatif
- url du vendeur externe

Par ailleurs, une méthode de recherche plus fine par tag
pourrait être implémentée pour définir et retrouver des produits 
mal repertoriés en traitant les "genres" definis dans le site. 

### Installation
* MongoDB 3.2
(par manque de temps)
```$ apt-get install mongodb```
* 3 librairies python complémentaires
listées dans requirements.pip
disponible via `pip`
```$ pip install -r requirements.pip```

### Configuration et test
python3 rakuten.py
retourne les informations demandées dans l'exercice
et les insèrent en base
à travers la methode collect_luxury()

Mais le script en question 
propose une protoimplementation d'API
example
``` code:python

	from rakuten import RakutenExtractor
	rk = RakutenExtractor()
    #search by brand every product
    
    #rk.search_brand("vuitton")
    #search by category every brand
    
    #rk.search_cat("fashiongoods")
    #search for a specific brand in a specific category
    #rk.search("fashiongoods", "vuitton")
    
    #Not implemented
    #rk.search_tag()
```
