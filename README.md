# Guide d'intégration - Templates Flask Banque

## Fichiers fournis

```
templates/
├── login.html       # Page de connexion
└── dashboard.html   # Tableau de bord (11 sections)
app.py               # Serveur Flask de test (avec données démo)
```

## Installation rapide (test)

```bash
pip install flask
python app.py
# Ouvrir http://localhost:5050
# Identifiant: client01 / Mot de passe: 123456
```

## Intégration dans votre projet Flask (Visual Studio)

### 1. Copier les templates
Placez `login.html` et `dashboard.html` dans votre dossier `templates/`.

### 2. Ajouter le filtre monétaire (optionnel)
Le dashboard utilise une macro Jinja2 intégrée `fmt()` pour formater les montants.
Si vous préférez un filtre Flask, ajoutez ceci dans votre `app.py` :

```python
@app.template_filter('money')
def money_filter(value):
    s = f"{float(value):,.2f}"
    s = s.replace(",", "\u00a0").replace(".", ",")
    return s
```

### 3. Routes Flask nécessaires

```python
# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET: afficher le formulaire
    # POST: vérifier identifiant/mot de passe
    return render_template('login.html', error=None)

# Tableau de bord
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html',
        user=user,               # dict: identifiant, nom, prenom, solde, carte_numero, carte_expiration
        transactions=transactions, # list of dict: id, date, operation, beneficiaire, reference, montant, type
        ribs=ribs,               # list of dict: id, prenom, nom, iban, bic, adresse
        prelevements=prelevements, # list of dict: id, creancier, description, montant, date_prochaine, frequence, statut
        epargnes=epargnes,       # list of dict: id, type, nom, solde, taux, plafond, date_ouverture
        credits=credits,         # list of dict: id, type, montant_initial, montant_restant, mensualite, taux, date_debut, date_fin, duree_mois, mois_restants
        assurances=assurances,   # list of dict: id, type, nom, prime_mensuelle, couverture, numero_contrat, date_echeance
        services=services,       # list of dict: id, type, date_demande, statut
        domiciliation=domiciliation, # dict: titulaire, email, adresse, code_postal, ville, pays, iban, bic, banque, agence, adresse_agence
        messages=messages,       # list of dict: id, titre, contenu, date, lu
        total_epargne=total_epargne, # float
        total_credits=total_credits,  # float
        unread_count=unread_count     # int
    )

# Déconnexion
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Routes AJAX (dashboard)
@app.route('/beneficiaire/add', methods=['POST'])     # Ajouter bénéficiaire
@app.route('/beneficiaire/delete/<id>', methods=['POST']) # Supprimer bénéficiaire
@app.route('/virement', methods=['POST'])              # Effectuer virement
@app.route('/prelevement/toggle/<id>', methods=['POST']) # Activer/Suspendre prélèvement
@app.route('/service/demande', methods=['POST'])       # Demander un service
@app.route('/message/read/<id>', methods=['POST'])     # Marquer message lu
@app.route('/credit/simulation', methods=['POST'])     # Simuler un crédit
```

### 4. Dépendances CDN (incluses dans les templates)
- **Tailwind CSS** : `https://cdn.tailwindcss.com` (styles)
- **Lucide Icons** : `https://unpkg.com/lucide@latest/dist/umd/lucide.js` (icônes)
- **Google Fonts** : Outfit (typographie)

Aucune installation npm nécessaire. Tout fonctionne via CDN.

## Structure des données

Référez-vous au fichier `app.py` pour voir le format exact de chaque type de données (USER, TRANSACTIONS, RIBS, etc.).
