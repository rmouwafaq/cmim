INTRODUCTION
============
Ce document a pour but de détailler le processus de calcul des cotisations, ainsi que de former les utilisateurs à configurer et utiliser les règles de calcul définies par le module Comptabilité auxiliaire sous Odoo.

 
Dictionnaire & Abréviations utilisés

Information	Explication & commentaire
SRP
RSC	Régime spécial Conjoint






 

Données de base
Ci-dessous nous allons présenter l’ensemble des entités de base qui permettent de structurer l’ensemble des données nécessaires à la gestion du système de calcul des cotisations de la CMIM.

Tables & notions structurantes

Secteur d’activité
==================

Les collectivités représentant l’ensemble des entreprises et administrations publiques sont organisés par secteur d’activité. La notion de secteur contient les informations suivantes :
Information	Explication & commentaire
Nom du secteur	Désignation
---------------------------
Plancher mensuel de cotisation	Base minimum mensuelle de cotisation
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Plancher trimestriel de cotisation	Base minimum Trimestrielle de cotisation
Plafond mensuel de cotisation	Base minimum mensuelle de cotisation
Plafond trimestriel de cotisation	Base minimum Trimestrielle de cotisation
Garanties	Composition de garanties possibles ou spéciale pour le secteur sélectionné


Garanties
Cette table recense les différenties garanties applicables au sein de la CMIM.
Information	Explication & commentaire
Code Garantie	A,B,C,D …
Libellé de la garantie	Désignation


Statut
Cette table référence les statuts qui décrivent un état donné, une qualité attribuée à un assuré et qui permet d’appliquer ou non une règle de calcul des cotisations. Les statuts permettent de définir et ou de limiter le champ d’application d’une règle de calcul aux seuls assurés disposant des statuts applicables en comparaison avec les statuts associés à cette même règle de cotisation.
Information	Explication & commentaire
Nom	Libellé
Régime	Normal ou RSC

Code	Abréviation pour désigner le statut

Constantes
Cette table recense les constantes utilisées dans le processus de calcul des cotisations.  En cas de changement, il est plus facile de les modifier.
  Information	Explication & commentaire
Code Garantie	A,B,C,D …
Libellé de la garantie	Désignation



Type de Périodes

  Information	Explication & commentaire
Nom	Désignation du type  période
Type de période	Mensuel – Trimestriel -


Périodes

  Information	Explication & commentaire
Nom	Désignation de la période
Type de période	Mensuel – Trimestriel -  à sélectionner parmi les types de période disponibles
Date début	Date début
Date Fin	Date Fin
Actif	Période active ou non



Assistant de génération de périodes

Le système est doté d’un processus de génération automatique des périodes.

L’assistant permet de constituer le référentiel de périodes qui seront utilisés par le système de calcul des cotisations, pour l’affectation des déclarations périodiques ou tout autre traitant nécessitant de référencer des périodes.
  Information	Explication & commentaire
Préfix de période	Désignation de la période
Type de période	Mensuel ou Trimestriel -  à sélectionner parmi les types de période disponibles
Durée de la période	Saisir un nombre constituant une durée représentant des périodes de base
Date début	Date de commencement des périodes
Nombre de période à générer 	Désigne le nombre de périodes à générer
Valider	Lancer l’exécution
Annuler 	Quitter l’assistant



Collectivités

 

UNE REGLE DE CALCUL C’EST QUOI ?
Afin de standardiser le processus de calcul des cotisations et pour rendre le système capable de gérer des éventuelles spécificités de calcul, nous avons modéliser une nouvelle entité qu’on a nommé REGLE DE CALCUL.
Une règle de calcul est une notion qui définit à la base un taux et une base de calcul pour permettre le calcul d’un montant :
Montant = Base * Taux%.

ARBORESCENCE DES REGLES DE CALCUL
Une règle de calcul peut avoir comme base de calcul le résultat d’une autre règle de calcul.
Exemple :
Considérant par exemple les deux règles suivantes :
•	RC1 : base = Salaire Brut, Taux : 10%
•	RC2 : base = RC1, taux = 50%
Avec un salaire de 10000 et sans application du prorata (nombre de jour déclaré = 30 sur une période d’un mois), le montant calculé avec RC1 vaut 10000*10% = 1000dh
Et donc le montant calculé pour RC2 va être égal à 1000*50% = 500dh
 

TYPES DES REGLES DE CALCUL
a.	Règle de calcul réservé système :
Ces règles de calcul ont été créées à la base pour permettre le calcul des bases de calcul spécifiques. Elles se comptent en quatre règles présentées comme suit :

Règle de calcul	Base de calcul associée	Cas d’utilisation
Salaire Brut	Salaire déclaré	Secteur complémentaire
Aucune	0	Tarif de type forfait
Salaire plafonné 	Salaire déclaré plafonné par les plancher et plafond du secteur de la collectivité
Tranche A	Salaire déclaré plafonné par le plafond CNSS (*)	Les produits de prévoyance
(Dans le contexte la CMIM) mais elles peuvent être utilisé pour n’importe quel produit
Tranche B	Différence entre Salaire et Tranche A à condition de ne pas dépasser la différence entre SRP (*) et la Tranche A	Les produits de prévoyance
(Dans le contexte la CMIM) mais elles peuvent être utilisé pour n’importe quel produit
(*) le plafond CNSS et le SRP sont considérés comme étant des constantes de calcul configurables.
b.	Règle de base
Comme son nom l’indique, une règle base permet en premier lieu de définir la base de calcul à utiliser pour calculer une cotisation. Elle définit également une règle de type tarif à prendre en considération pour décider le taux de calcul.
CAPTURE
c.	Règle Tarif
L’objectif de mettre en place des règles tarifs est de pouvoir définir des taux par défaut utilisés automatiquement au cours du processus de calcul, si aucun tarif n’a été affecté au paramétrage de la collectivité.
CAPTURE
d.	Règle d’abattement
Une légère différence est constatée pour ce type de règles puisqu’ici, on ne parle pas de base de calcul, on ne parle que du tarif, qui doit être obligatoirement en pourcentage cette fois-ci, et qui va être appliqué sur le résultat de calcul de toute règle de base avec une applicabilité abattement activée. (Voir le chapitre Applicabilité des règles de calcul).
CAPTURE
e.	Règle spéciale
Les règles spéciales sont réservées pour gérer les spécificités de calcul pour le régime spécial conjoint.
CAPTURE
APPLICABILITE DES REGLES DE CALCUL ET PRORATA
CAPTURE
Le paramétrage offert permet de restreindre l’applicabilité d’une règle de calcul par garantie, secteurs et par statuts, A noter que quand rien n’est définit la règle est toujours applicable, en d’autres termes, si aucun secteur n’a été définit dans l’applicabilité d’une règle donnée, celle-ci va être applicables pour tous les secteurs.
On peut également définir des dates de début et de fin de validité à une règle de calcul, et ce pour gérer des anciennes règles qui ne sont plus applicables en 2017 par exemple.
Pour les règles de type base, deux propriétés de plus peuvent être ajoutées au paramétrage d’applicabilité, à savoir l’applicabilité d’un abattement, et l’applicabilité du prorata.
Si l’applicabilité d’abattement est définie pour règle de base, l’ensembles des règles d’abattement qui figure dans le paramétrage de la collectivité va être appliqué sur le résultat de calcul de ladite règle de base.
L’applicabilité du prorata permet de gérer les déclarations de salaire avec un nombre de jours déclaré inférieur au nombre de jour de la période.

DEFINIR DES CONTRATS
Un contrat est une entité qui définit à priori l’engagement d’un adhérent de la CMIM à des lignes de contrat, qui regroupent des produits à des règles de calcul.
A noter que les contrats peuvent être génériques, vu qu’on peut associer un seul contrat à plusieurs collectivités adhérentes. C’est dans le paramétrage de la collectivité qu’on changera les taux qui diffèrent. (Voir partie génération des tarifs ci-dessous)
CAPTURE
Générateur des tarifs
Le générateur de tarifs est un petit programme qui permet de paramétrer une collectivité par des tarifs différentes que celle figurant dans le contrat.
Exemple :
CAPTURE

PROCESSUS GLOBAL

PROCESSUS DE CALCUL DES COTISATIONS


