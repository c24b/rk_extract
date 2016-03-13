#RK challenge

##Contextes
Rakuten.py est un mini script qui consitue
une proto-api d'interrogation et d'extraction de données
issues de la plateforme rakuten.co.jp
ce script propose plusieurs méthodes d'interrogation et d'extraction 
des données. 
Le site en question ne pose pas de problème particulier
- dans son accès: tout est disponible sans avoir besoin 
d'émuler un navigateur (pas besoin d'un selenium donc)
- dans sa recherche:
les parametres de recherche de produits sont tous disponibles dans l'url
et procèdent d'une nomenclature bien détaillée facile à reproduire
* 231 marques référencées (brand)
* 35 categories (category)
* 417 magasins principaux (mall)
* 3944 magasins spécifiques (store)

- dans ses pages:
les tags utilisés sont suffisamments spécifiques pour accéder à une 
information qualifiée qui permet des analyses de répartition
par marque
par type de produit (niveau 0, ex:bag niveau 1 ex: luxury bag )
par categorie (ex: fashiongoods)


## Implémentation
Nous avons donc simplement utilisé: 
requests et beautifulsoup4 (parser au dessus de lxml) pour l'extraction des pages web
via une methode parse commune au deux objets qui prend en compte les différences d'encodage selon les pages 
(UTF-8 ou euc_jisx0213)
Une base de données de type Mongo pour collecter dans un premier temps 
le référentiel de base en utilisant le driver python pymongo
et dans un deuxième temps la liste des produits issus d'une recherche
Un module simple de detection de lang appelé langdetect
Tous disponible via pip

Deux objets sont donc disponible:
Une methode d'extraction du référentiel de base 

Une méthode de recherche et d'extraction des produits disponibles 
en fonction de cette recherche
qui stocke les produits disponibles dans une table produits
et renvoie les résultats de la recherche
ainsi que dans le cas d'une marque la répartition des produits trouvés 
en fonction de leur catégories, type de produit (niveau 0 ou 1)

Face au travail qui a été demandé extraire les sacs de luxe féminin revient
à faire une recherche dans le magazin spécifique
la liste des marques disponibles et référencées
da



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


Le script en question 
propose une proto-implementation d'API
example
``` code:python

	from rakuten import RakutenExtractor
	rk = RakutenAPI()
    #search by brand every product
    
    #rk.search(brand="vuitton")
    #search by category every brand
    
    #rk.search(category="fashiongoods")
    #search for a specific brand in a specific category
    #rk.search(category="fashiongoods", brand="vuitton")
    
    #rk.search_tag()
```
Pour 
