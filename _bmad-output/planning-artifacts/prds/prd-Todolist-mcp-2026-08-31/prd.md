---
title: Todolist MCP - Gestion de listes de tâches par LLM
created: 2026-08-31
updated: 2026-09-01
status: final
---

# PRD: Todolist MCP
*Gestion de listes de tâches pour LLM via serveur MCP*

## 0. Document Purpose

Ce document définit les exigences pour **Todolist MCP**, un serveur MCP en Python qui permet aux LLM de gérer des listes de tâches pour un utilisateur individuel. 

**Structure du document :**
- Vocabulaire ancré dans le Glossaire (§3)
- Fonctionnalités regroupées avec FR (Functional Requirements) numérotées globalement (§4)
- Les hypothèses sont taggées en ligne avec `[ASSUMPTION: ...]` et indexées en (§9)

**Public cible :** Développeur du projet (vous), futur maintainer, et l'LLM lui-même comme consommateur final.

**Niveau de rigueur :** Projet personnel/hobby - document concis (2-3 pages), axé sur l'essentiel pour implémentation rapide.

---

## 1. Vision

Todolist MCP est un **serveur MCP léger** qui donne aux LLM la capacité de gérer des listes de tâches de manière naturelle et intuitive. L'utilisateur peut dialoguer avec son LLM préféré (via une interface compatible MCP) pour :

- **Consulter** ses tâches du jour, de demain, ou de toute période
- **Ajouter** des tâches par conversation naturelle (*"Rappelle-moi d'acheter du pain"*)
- **Mettre à jour** l'état des tâches (*"J'ai acheté le pain, marque la tâche comme terminée"*)
- **Prioriser** et **organiser** ses tâches avec des dates d'échéance

Le projet élimine la friction de basculer vers une application de todo séparée : **tout se passe dans la conversation avec le LLM**. L'expérience est fluide, sans interface utilisateur dédiée, uniquement via des appels MCP transparents.

**Pourquoi ce projet ?** 
- Centraliser la gestion des tâches dans l'outil que l'utilisateur utilise déjà (son LLM)
- Éviter la fragmentation des notes et rappels dans différents outils
- Expérimenter avec les capacités MCP pour des cas d'usage concrets

**Valeur clé :** *La gestion des tâches devient invisible - elle fait simplement partie de la conversation.*

---

## 2. Target User

### 2.1 Jobs To Be Done

- **JTBD-1 :** "Je veux pouvoir demander à mon LLM ce que je dois faire aujourd'hui, sans avoir à ouvrir une autre application"
- **JTBD-2 :** "Je veux que mon LLM se souvienne de me rappeler quelque chose, et me le rappelle au bon moment"
- **JTBD-3 :** "Je veux marquer une tâche comme terminée naturellement, sans command line ou UI"
- **JTBD-4 :** "Je veux prioriser mes tâches et gérer leurs échéances directement via conversation"
- **JTBD-5 :** "Je veux intégrer la gestion des tâches dans mon application personnalisée via une API HTTP"

### 2.2 Non-Users (v1)

- Les équipes ou organisations (multi-utilisateurs)
- Les utilisateurs nécessitant des fonctionnalités avancées (rappels automatiques, répétition de tâches, partage)
- Les utilisateurs non-techniques sans accès à un client MCP

### 2.3 Key User Journeys

**UJ-1. Jean consulte ses tâches du jour avant de commencer sa journée**
- **Persona + contexte :** Jean, développeur utilisant un LLM quotidiennement, veut organiser sa journée de travail.
- **Entry state :** Jean a démarré sa session avec son client LLM (compatible MCP) via stdio. Aucun token requis en local.
- **Path :** 
  1. Jean demande : "Quelles sont mes tâches pour aujourd'hui ?"
  2. Le LLM interroge Todolist MCP via l'outil `get_tasks` avec filtre `due_date: today`
  3. MCP retourne la liste des tâches : ["Finir le PR #42", "Appeler le client Martin", "Acheter du lait"]
  4. Le LLM formate et présente les tâches à Jean
- **Climax :** Jean voit ses 3 tâches du jour avec leurs priorités et échéances
- **Resolution :** Jean décide de commencer par le PR #42. Il demande : "Quelle est la tâche la plus prioritaire ?"

**UJ-2. Jean ajoute une tâche depuis sa conversation**
- **Persona + contexte :** Jean pense à quelque chose d'important pendant sa conversation avec le LLM.
- **Entry state :** Session MCP active via stdio.
- **Path :**
  1. Jean dit : "Rappelle-moi de vérifier les logs de production à 15h"
  2. Le LLM détecte l'intention d'ajout de tâche
  3. Le LLM appelle `create_task` avec title="Vérifier les logs de production", due_date="2026-08-31T15:00:00", priority="high"
  4. MCP confirme la création avec l'ID de la tâche
  5. Le LLM confirme à Jean : "Tâche ajoutée : 'Vérifier les logs de production' pour 15h aujourd'hui"
- **Climax :** La tâche est persistée en base de données
- **Resolution :** Jean peut maintenant voir cette tâche dans ses listes

**UJ-3. Jean marque une tâche comme terminée**
- **Persona + contexte :** Jean a terminé une tâche et veut la marquer comme complète.
- **Entry state :** Session MCP active, tâche "Acheter du pain" existe avec status="pending"
- **Path :**
  1. Jean dit : "J'ai acheté le pain, tu peux cocher la tâche"
  2. Le LLM identifie la tâche "Acheter du pain" (par matching de texte)
  3. Le LLM appelle `update_task` avec task_id=<id>, status="completed"
  4. MCP met à jour la tâche en base
  5. Le LLM confirme : "Tâche 'Acheter du pain' marquée comme terminée ✓"
- **Climax :** Le status de la tâche passe à "completed"
- **Resolution :** La tâche n'apparaîtra plus dans les requêtes "tâches en cours"

**UJ-4. Jean utilise le serveur MCP via HTTP pour une intégration personnalisée**
- **Persona + contexte :** Jean, développeur, veut intégrer Todolist MCP dans son application personnalisée via HTTP.
- **Entry state :** Serveur Todolist MCP démarré en mode HTTP sur le port 8080, token valide généré.
- **Path :**
  1. Jean envoie une requête POST à `http://localhost:8080/mcp/call` avec header `Authorization: Bearer <token>`
  2. Le body contient : `{"tool": "list_tasks", "arguments": {"due_date": "today"}}`
  3. Le serveur MCP traite la requête et retourne la liste des tâches du jour
  4. Jean reçoit la réponse JSON avec les tâches
- **Climax :** L'application de Jean affiche les tâches du jour
- **Resolution :** Jean peut maintenant intégrer la gestion des tâches dans son application

---

## 3. Glossary

- **Tâche (Task)** : Une unité de travail ou de rappel à accomplir. Contient obligatoirement un titre, et optionnellement : description, priorité, date d'échéance, status.
- **Status de tâche** : État d'une tâche. Valeurs possibles : `pending` (par défaut), `completed`, `cancelled`. Une tâche `completed` ne peut pas être modifiée.
- **Priorité** : Niveau d'importance d'une tâche. Valeurs : `low`, `medium`, `high`, `critical`. Ordre : low < medium < high < critical.
- **Date d'échéance (Due Date)** : Date et heure limite pour accomplir une tâche. Format simplifié local : `YYYY-MM-DD HH:MM:SS`. Peut être `null` pour les tâches sans échéance. Le serveur interprète les dates dans le timezone local de la machine.
- **Serveur MCP** : Serveur implémentant le Model Context Protocol, permettant aux LLM d'appeler des outils définis.
- **Outil MCP (Tool)** : Fonction exposée par le serveur MCP que le LLM peut appeler. Chaque outil a un nom, une description, et un schéma d'entrée/sortie.
- **Token d'authentification** : Chaîne secrète permettant à un client MCP de s'authentifier auprès du serveur. En v1 : un seul token valide pour l'utilisateur unique, généré via CLI. Requis uniquement pour le transport HTTP ; le transport stdio local n'en exige pas.
- **Transport stdio** : Méthode de communication standard via stdin/stdout, utilisée par défaut par MCP.
- **Transport HTTP** : Méthode de communication alternative via protocole HTTP, permettant une intégration plus flexible avec des clients distants ou des architectures microservices.
- **Endpoint HTTP** : URL accessible exposant les outils MCP via HTTP (ex: `POST /mcp/call`).

---

## 4. Features

### 4.1 Gestion de base des tâches
**Description :** Fonctionnalités CRUD (Create, Read, Update, Delete) pour les tâches. Permet au LLM de manipuler complètement le cycle de vie des tâches. Réalise UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-1: Créer une tâche

Le LLM peut créer une nouvelle tâche avec un titre, une description optionnelle, une priorité, et une date d'échéance optionnelle. Réalise UJ-2.

**Consequences (testable):**
- Le serveur MCP expose un outil `create_task` acceptant : title (requis), description, priority, due_date
- Le serveur retourne un task_id unique (UUID v4) pour chaque tâche créée
- Si un task_id est fourni par le LLM, le serveur l'ignore et génère un nouvel UUID v4 automatiquement
- La tâche est persistée en base de données avec status="pending"
- La tâche créée apparaît dans les résultats de `get_tasks` et `list_tasks`

**Out of Scope:**
- Validation avancée du contenu (ex: longueur max du titre)
- Détection automatique de doublons

#### FR-2: Lire une tâche spécifique

Le LLM peut récupérer les détails d'une tâche spécifique par son ID. 

**Consequences (testable):**
- Le serveur MCP expose un outil `get_task` acceptant task_id (requis)
- Le serveur retourne toutes les propriétés de la tâche ou une erreur 404 si non trouvée
- Les propriétés retournées incluent : task_id, title, description, priority, due_date, status, created_at, updated_at

#### FR-3: Lister les tâches

Le LLM peut lister les tâches avec des filtres optionnels. Réalise UJ-1.

**Consequences (testable):**
- Le serveur MCP expose un outil `list_tasks` acceptant des filtres optionnels : status, priority, due_date (exact ou range), limit, offset
- Le serveur retourne un tableau de tâches avec pagination (default limit=50, offset=0)
- **Pas de limite maximale** sur le nombre total de tâches (choix v1 pour projet personnel)
- Les tâches sont triées par due_date ASC (échéance la plus proche en premier), puis par priority DESC (priorité la plus haute en premier)
- Les filtres peuvent être combinés (AND logique)

#### FR-4: Mettre à jour une tâche

Le LLM peut modifier les propriétés d'une tâche existante. Réalise UJ-3.

**Consequences (testable):**
- Le serveur MCP expose un outil `update_task` acceptant task_id (requis) et n'importe quelle combinaison de : title, description, priority, due_date, status
- Le serveur retourne la tâche mise à jour avec updated_at mis à jour
- Une tâche avec status="completed" ne peut pas être modifiée (retourne erreur 400)
- Le task_id ne peut pas être modifié

#### FR-5: Supprimer une tâche

Le LLM peut supprimer une tâche de manière irréversible.

**Consequences (testable):**
- Le serveur MCP expose un outil `delete_task` acceptant task_id (requis)
- Le serveur retourne un message de confirmation ou une erreur 404 si non trouvée
- La tâche supprimée n'apparaît plus dans aucun résultat de `list_tasks` ou `get_task`

#### FR-6: Marquer une tâche comme complétée

Le LLM peut marquer une tâche comme terminée. Réalise UJ-3.

**Consequences (testable):**
- Le serveur MCP expose un outil `complete_task` acceptant task_id (requis)
- Le serveur met à jour status="completed" et updated_at
- Une tâche déjà complétée retourne une erreur 400

**Feature-specific NFRs:**
- Performance : Tous les appels aux outils MCP doivent répondre en < 500ms pour un jeu de données de < 1000 tâches

**Notes:**
- [ASSUMPTION: Le LLM est capable de parser les requêtes utilisateur pour extraire les paramètres nécessaires aux appels MCP]
- [ASSUMPTION: Le matching de tâche pour UJ-3 se fait par similarité de texte sur le titre]

### 4.2 Gestion de la priorité
**Description :** Permet au LLM et à l'utilisateur de prioriser les tâches efficacement.

**Functional Requirements:**

#### FR-7: Définir la priorité à la création

Le LLM peut spécifier une priorité lors de la création d'une tâche (FR-1).

**Consequences (testable):**
- Le paramètre priority accepte les valeurs : low, medium, high, critical
- Si non spécifié, default = medium

#### FR-8: Modifier la priorité d'une tâche existante

Le LLM peut changer la priorité d'une tâche via `update_task` (FR-4).

### 4.3 Gestion des dates d'échéance
**Description :** Permet de gérer le temps et l'urgence des tâches.

**Functional Requirements:**

#### FR-9: Définir une date d'échéance à la création

Le LLM peut spécifier une date d'échéance lors de la création d'une tâche (FR-1).

**Consequences (testable):**
- Le paramètre due_date accepte un timestamp au format simplifié local : `YYYY-MM-DD HH:MM:SS`
- Si non spécifié, default = null (pas d'échéance)
- Les dates sont interprétées dans le timezone local de la machine hôte

#### FR-10: Filtrer les tâches par date

Le LLM peut filtrer les tâches par date via `list_tasks` (FR-3).

**Consequences (testable):**
- Le filtre due_date accepte :
  - Une date exacte (ex: "2026-08-31") pour les tâches échant à cette date
  - Une plage (ex: "2026-08-31..2026-09-02") pour les tâches échant dans l'intervalle
  - "today" pour les tâches échant aujourd'hui (basé sur la date locale)
  - "tomorrow" pour les tâches échant demain (basé sur la date locale)
  - "overdue" pour les tâches dont due_date < now() et status="pending" (comparaison basée sur l'heure locale)

#### FR-11: Mettre à jour la date d'échéance

Le LLM peut modifier la date d'échéance d'une tâche via `update_task` (FR-4).

### 4.4 Authentification
**Description :** Sécuriser l'accès distant au serveur MCP (transport HTTP) pour protéger les données de l'utilisateur unique. Le transport stdio local est considéré de confiance et n'exige pas d'authentification.

**Functional Requirements:**

#### FR-12: Authentification par token (transport HTTP)

Le serveur MCP requiert un token d'authentification valide uniquement pour les appels reçus via le transport HTTP. Le transport stdio, utilisé localement par un client MCP de confiance, n'exige pas de token.

**Consequences (testable):**
- En mode `http` ou `both`, le serveur vérifie le token avant toute exécution d'outil
- En mode `stdio`, les outils sont accessibles sans token (transport local de confiance)
- Un token invalide ou manquant sur HTTP retourne une erreur 401 Unauthorized
- **Pas de rotation automatique du token** en v1 (mono-utilisateur, risque sécurité acceptable)

#### FR-13: Génération du token via CLI

L'application permet de générer un token d'authentification unique via une commande en ligne de commande.

**Consequences (testable):**
- Une commande `todolist-mcp generate-token` génère un nouveau token unique
- Le token est affiché à l'utilisateur et stocké dans un fichier de configuration local
- Le token généré est valide immédiatement pour l'authentification MCP
- Un avertissement est affiché si un token existe déjà (écrasement)

**Notes:**
- Un seul token est nécessaire pour v1 (mono-utilisateur)
- Le token est stocké dans un fichier de configuration local (ex: `~/.todolist-mcp/token`)

### 4.5 Support du protocole HTTP
**Description :** Permettre au serveur MCP de communiquer via HTTP en plus du transport stdio standard, pour une intégration plus flexible avec des clients distants ou des architectures modernes.

**Functional Requirements:**

#### FR-14: Support du transport HTTP

Le serveur MCP peut être configuré pour exposer ses outils via HTTP en plus de stdio.

**Consequences (testable):**
- Le serveur expose un endpoint HTTP POST `/mcp/call` pour l'exécution des outils
- Le serveur expose un endpoint HTTP GET `/mcp/tools` pour lister les outils disponibles
- Le serveur expose un endpoint HTTP GET `/mcp/tools/{tool_name}` pour obtenir le schéma d'un outil spécifique
- Le serveur accepte les requêtes HTTP avec headers `Content-Type: application/json`
- Les réponses HTTP sont au format JSON avec le bon status code

#### FR-15: Authentification HTTP

Les requêtes HTTP nécessitent une authentification valide.

**Consequences (testable):**
- Le serveur accepte le token d'authentification via header HTTP `Authorization: Bearer <token>`
- Le serveur accepte le token d'authentification via paramètre de requête `?token=<token>`
- Le header `Authorization` a la priorité sur le paramètre de requête
- Un token invalide ou manquant retourne un status HTTP 401 Unauthorized

#### FR-16: Configuration du mode de transport

L'utilisateur peut choisir le mode de transport au démarrage du serveur.

**Consequences (testable):**
- Le serveur accepte un paramètre de configuration `--transport` avec valeurs : `stdio` (défaut), `http`, ou `both`
- En mode `http`, le serveur démarre un serveur HTTP sur un port configurable (défaut: 8080)
- En mode `both`, le serveur gère simultanément stdio et HTTP
- En mode `stdio`, le serveur fonctionne comme avant (comportement par défaut)

**Feature-specific NFRs:**
- Performance : Les appels HTTP doivent répondre en < 500ms pour un jeu de données de < 1000 tâches
- Sécurité : Le serveur HTTP doit désactiver CORS par défaut pour une utilisation locale
- Configuration : Le port HTTP doit être configurable via variable d'environnement `TODOLIST_MCP_HTTP_PORT`

**Notes:**
- [ASSUMPTION: Le serveur HTTP utilise FastAPI ou un framework similaire pour la gestion des routes]
- [ASSUMPTION: Le transport HTTP suit les conventions MCP pour la sérialisation des requêtes/réponses]

---

## 5. Non-Goals (Explicit)

- **Multi-utilisateurs** : Pas de gestion de plusieurs utilisateurs en v1
- **Rappels automatiques** : Pas de système de notifications proactives (rappels par email, push, etc.)
- **Tâches répétitives** : Pas de support pour les tâches récurrentes (daily, weekly, etc.)
- **Partage de tâches** : Pas de fonctionnalité de partage ou collaboration
- **Interface utilisateur** : Pas de UI web, CLI, ou mobile - uniquement accès via MCP
- **Synchronisation** : Pas de sync avec d'autres services (Google Tasks, Todoist, etc.)
- **Historique des tâches** : Pas d'archivage automatique des tâches complétées
- **Recherche full-text** : Pas de recherche avancée sur le contenu des tâches
- **Tags/Catégories** : Pas de système de tagging ou catégorisation en v1

---

## 6. MVP Scope

### 6.1 In Scope

✅ Serveur MCP en Python avec tous les outils définis (§4)
✅ Base de données SQLite pour la persistance
✅ Authentification par token unique (transport HTTP uniquement)
✅ Gestion complète CRUD des tâches
✅ Gestion de la priorité (4 niveaux)
✅ Gestion des dates d'échéance
✅ Filtres de base pour `list_tasks`
✅ Tri intelligent par échéance et priorité
✅ Documentation des outils MCP (pour le LLM)
✅ Support du transport HTTP avec endpoints RESTful
✅ Authentification HTTP via headers ou paramètres
✅ Configuration flexible du mode de transport (stdio/HTTP/both)

### 6.2 Out of Scope for MVP

❌ Multi-utilisateurs - [NOTE FOR PM: À considérer pour v2 si besoin partagé]
❌ Rappels automatiques - Complexité ajoutée non essentielle pour le MVP
❌ Tâches récurrentes - [NOTE FOR PM: Feature populaire mais complexe, déferrée à v2]
❌ Interface autre que MCP - Le focus est 100% sur l'intégration LLM
❌ Synchronisation externe - Intégrations tierces non prioritaires

---

## 7. Success Metrics

**Primary**
- **SM-1**: 100% des fonctionnalités CRUD fonctionnelles et testées. Valide FR-1 à FR-6.
- **SM-2**: Temps de réponse moyen des outils MCP < 100ms pour < 100 tâches. Valide FR-1 à FR-11.
- **SM-3**: L'utilisateur peut accomplir UJ-1, UJ-2, UJ-3, UJ-4 sans erreur. Valide tous les FR.
- **SM-4**: 100% des endpoints HTTP fonctionnels et testés. Valide FR-14 à FR-16.

**Secondary**
- **SM-4**: Couverture de tests unitaires > 80%. Valide la qualité du code.
- **SM-5**: Documentation complète des outils MCP pour le LLM. Valide l'usabilité.

**Counter-metrics (do not optimize)**
- **SM-C1**: Nombre de tâches en base - ne pas optimiser pour le volume, mais pour la qualité de l'expérience utilisateur.
- **SM-C2**: Temps de développement - ne pas sacrifier la qualité pour aller vite.

---

## 8. Open Questions

*Aucune question ouverte - toutes résolues.*

---

## 9. Assumptions Index

*Tous les `[ASSUMPTION]` du document ont été validés :*

- **§4.1** : Le LLM est capable de parser les requêtes utilisateur pour extraire les paramètres nécessaires aux appels MCP ✅
- **§4.1** : Le matching de tâche pour UJ-3 se fait par similarité de texte sur le titre ✅
- **§4.5** : Le serveur HTTP utilise FastAPI ou un framework similaire pour la gestion des routes 🔄
- **§4.5** : Le transport HTTP suit les conventions MCP pour la sérialisation des requêtes/réponses 🔄
