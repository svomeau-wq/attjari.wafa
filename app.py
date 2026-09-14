import os
import base64
from datetime import datetime

import resend
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from fpdf import FPDF

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

resend.api_key = RESEND_API_KEY

app = Flask(__name__)

app.secret_key = 'banque-secret-key-change-me'

# ======================
# CONFIG RESEND EMAIL
# ======================


# Filtre Jinja2 pour formatage monetaire
@app.template_filter('money')
def money_filter(value):
    try:
        s = f"{float(value):,.2f}"
        s = s.replace(",", " ").replace(".", ",")
        return s
    except (ValueError, TypeError):
        return "0,00"


# ======================
# PDF + EMAIL
# ======================
def fmt_money(value):
    s = f"{float(value):,.2f}"
    return s.replace(",", " ").replace(".", ",")


def generer_pdf_virement(data):
    if FPDF is None:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # En-tete
    pdf.set_fill_color(209, 0, 0)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_y(10)
    pdf.cell(0, 10, 'Attijariwafa Bank', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, 'Confirmation de virement', 0, 1, 'C')

    # Corps
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(50)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Details du virement', 0, 1, 'L')
    pdf.line(10, 62, 200, 62)
    pdf.ln(5)

    pdf.set_font('Helvetica', '', 11)
    lignes = [
        ('Date', datetime.now().strftime('%d/%m/%Y %H:%M')),
        ('Beneficiaire', data.get('prenom', '') + ' ' + data.get('nom', '')),
        ('IBAN', data.get('iban', '')),
        ('BIC', data.get('bic', '')),
        ('Montant', fmt_money(data.get('montant', 0)) + ' EUR'),
        ('Reference', data.get('reference', '-')),
        ('Motif', data.get('motif', '-')),
    ]

    for label, valeur in lignes:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(50, 8, label, 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, valeur, 0, 1)

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, 'Ce document est une confirmation automatique.', 0, 1, 'C')
    pdf.cell(0, 6, "Attijariwafa Bank - est un groupe bancaire marocain actif dans la banque de détail, la banque d'investissement", 0, 1, 'C')

    return pdf.output()


def envoyer_email_confirmation(email_dest, data):
    try:
        pdf_bytes = generer_pdf_virement(data)
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8') if pdf_bytes else None

        nom_complet = data.get('prenom', '') + ' ' + data.get('nom', '')
        montant_fmt = fmt_money(data.get('montant', 0))

        html_body = (
            '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">'
            '<div style="background:#d10000;padding:30px;text-align:center">'
            '<h1 style="color:white;margin:0">Attijariwafa Bank</h1>'
            '<p style="color:rgba(255,255,255,0.8);margin:5px 0 0">Confirmation de virement</p>'
            '</div>'
            '<div style="padding:30px;background:#f8fafc">'
            '<h2 style="color:#0f172a;margin-top:0">Virement effectue avec succes</h2>'
            '<div style="background:white;border:1px solid #e2e8f0;border-radius:8px;padding:20px">'
            '<table style="width:100%;border-collapse:collapse">'
            '<tr><td style="padding:8px 0;color:#64748b;width:140px"><strong>Beneficiaire</strong></td>'
            '<td style="padding:8px 0;color:#0f172a">' + nom_complet + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#64748b"><strong>Montant</strong></td>'
            '<td style="padding:8px 0;color:#d10000;font-size:18px;font-weight:bold">' + montant_fmt + ' EUR</td></tr>'
            '<tr><td style="padding:8px 0;color:#64748b"><strong>IBAN</strong></td>'
            '<td style="padding:8px 0;color:#0f172a;font-family:monospace">' + data.get('iban', '') + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#64748b"><strong>Reference</strong></td>'
            '<td style="padding:8px 0;color:#0f172a">' + data.get('reference', '-') + '</td></tr>'
            '<tr><td style="padding:8px 0;color:#64748b"><strong>Motif</strong></td>'
            '<td style="padding:8px 0;color:#0f172a">' + data.get('motif', '-') + '</td></tr>'
            '</table>'
            '</div>'
            '<p style="color:#64748b;font-size:12px;text-align:center;margin-top:20px">'
            'Ce message est une confirmation automatique. Ne pas repondre.</p>'
            '</div>'
            '</div>'
        )

        params = {
            'from': SENDER_EMAIL,
            'to': [email_dest],
            'subject': 'Confirmation de virement - ' + montant_fmt + ' EUR',
            'html': html_body,
        }

        if pdf_b64:
            params['attachments'] = [{
                'filename': 'confirmation_virement.pdf',
                'content': pdf_b64,
            }]

        result = resend.Emails.send(params)
        print('Email envoye avec succes: ' + str(result))
        return True
    except Exception as e:
        print('Erreur envoi email: ' + str(e))
        return False


# ======================
# DONNEES DEMO
# ======================
USER = {
    'identifiant': 'client01',
    'nom': 'Christina',
    'prenom': 'GEZELUIS',
    'solde': 1752500
,
    'carte_numero': '**** **** **** 4589',
    'carte_expiration': '12/28',
    'email': 'christinagezeluis@gmail.com',
}

TRANSACTIONS = [
    {'id': '1', 'date': '2026-06-23', 'operation': 'Virement émis - banque', 'beneficiaire': 'Francisco Becona', 'reference': 'SAL-2026-01', 'montant': 158000.00, 'type': 'debit'},
    {'id': '2', 'date': '2026-01-14', 'operation': 'Prelevement EDF', 'beneficiaire': 'EDF', 'reference': 'EDF-2026-01', 'montant': -85.50, 'type': 'debit'},
    {'id': '3', 'date': '2026-01-13', 'operation': 'Carte bancaire - Carrefour', 'beneficiaire': 'Carrefour', 'reference': 'CB-20260113', 'montant': -156.30, 'type': 'debit'},
    {'id': '4', 'date': '2026-01-12', 'operation': 'Virement emis', 'beneficiaire': 'Marie Martin', 'reference': 'VIR-2026-003', 'montant': -500.00, 'type': 'debit'},
    {'id': '5', 'date': '2026-01-10', 'operation': 'Remboursement Amazon', 'beneficiaire': 'Amazon', 'reference': 'RMB-2026-01', 'montant': 45.99, 'type': 'credit'},
]

RIBS = [
    {'id': '1', 'prenom': 'Marie', 'nom': 'Martin', 'iban': 'FR76 3000 6000 0112 3456 7890 189', 'bic': 'AGRIFRPP', 'adresse': '12 rue de la Paix, 75002 Paris'},
    {'id': '2', 'prenom': 'Pierre', 'nom': 'Durand', 'iban': 'FR76 2004 1010 0505 0001 3M02 606', 'bic': 'PSSTFRPP', 'adresse': ''},
]

PRELEVEMENTS = [
    {'id': '1', 'creancier': 'EDF', 'description': 'Electricite - Contrat principal', 'montant': 85.50, 'date_prochaine': '2026-02-14', 'frequence': 'Mensuel', 'statut': 'actif'},
    {'id': '2', 'creancier': 'Orange', 'description': 'Forfait mobile + internet', 'montant': 59.99, 'date_prochaine': '2026-02-05', 'frequence': 'Mensuel', 'statut': 'actif'},
    {'id': '3', 'creancier': 'Netflix', 'description': 'Abonnement streaming', 'montant': 13.49, 'date_prochaine': '2026-02-01', 'frequence': 'Mensuel', 'statut': 'actif'},
    {'id': '4', 'creancier': 'AXA', 'description': 'Assurance habitation', 'montant': 35.00, 'date_prochaine': '2026-02-20', 'frequence': 'Mensuel', 'statut': 'actif'},
    {'id': '5', 'creancier': 'Salle de Sport', 'description': 'Abonnement fitness', 'montant': 29.90, 'date_prochaine': '2026-02-01', 'frequence': 'Mensuel', 'statut': 'suspendu'},
]

EPARGNES = [
    {'id': '1', 'type': 'livret_a', 'nom': 'Livret A', 'solde': 15780.50, 'taux': 3.0, 'plafond': 22950, 'date_ouverture': '2018-03-15'},
    {'id': '2', 'type': 'ldds', 'nom': 'LDDS', 'solde': 8500.00, 'taux': 3.0, 'plafond': 12000, 'date_ouverture': '2019-06-20'},
    {'id': '3', 'type': 'pel', 'nom': 'PEL', 'solde': 25000.00, 'taux': 2.0, 'plafond': 61200, 'date_ouverture': '2020-01-10'},
    {'id': '4', 'type': 'assurance_vie', 'nom': 'Assurance Vie', 'solde': 45000.00, 'taux': 2.5, 'plafond': 0, 'date_ouverture': '2017-09-01'},
]

CREDITS = [
    {'id': '1', 'type': 'immobilier', 'montant_initial': 200000, 'montant_restant': 145000, 'mensualite': 850.00, 'taux': 1.8, 'date_debut': '2022-01-15', 'date_fin': '2042-01-15', 'duree_mois': 240, 'mois_restants': 192},
    {'id': '2', 'type': 'auto', 'montant_initial': 15000, 'montant_restant': 8500, 'mensualite': 280.00, 'taux': 3.5, 'date_debut': '2024-06-01', 'date_fin': '2029-06-01', 'duree_mois': 60, 'mois_restants': 42},
]

ASSURANCES = [
    {'id': '1', 'type': 'habitation', 'nom': 'Habitation Premium', 'prime_mensuelle': 35.00, 'couverture': 'Tous risques habitation, degats des eaux, incendie, vol', 'numero_contrat': 'HAB-2024-001', 'date_echeance': '2026-12-31'},
    {'id': '2', 'type': 'auto', 'nom': 'Auto Tous Risques', 'prime_mensuelle': 75.00, 'couverture': 'Responsabilite civile, bris de glace, vol, incendie', 'numero_contrat': 'AUT-2024-002', 'date_echeance': '2026-06-30'},
    {'id': '3', 'type': 'vie', 'nom': 'Vie Serenite', 'prime_mensuelle': 100.00, 'couverture': 'Capital deces, invalidite permanente, rente education', 'numero_contrat': 'VIE-2024-003', 'date_echeance': '2046-01-01'},
    {'id': '4', 'type': 'sante', 'nom': 'Mutuelle Sante Plus', 'prime_mensuelle': 85.00, 'couverture': 'Hospitalisation, optique, dentaire, medecines douces', 'numero_contrat': 'SAN-2024-004', 'date_echeance': '2026-12-31'},
]

SERVICES = [
    {'id': '1', 'type': 'chequier', 'date_demande': '2026-01-10', 'statut': 'livre'},
    {'id': '2', 'type': 'attestation', 'date_demande': '2026-01-05', 'statut': 'en_cours'},
]

DOMICILIATION = {
    'titulaire': 'Christina Gezeluis',
    'email': 'christinagezeluis@gmail.com',
    'adresse': '55 Bd Abdelmoumen, Casablanca 20100, Maroc',
    'code_postal': '20100',
    'ville': 'Casablanca',
    'pays': 'Maroc',
    'iban': 'MA76 1234 5678 9012 3456 7890 123',
    'bic': 'BCMAMAMCXXX',
    'banque': 'Attijariwafa Bank',
    'agence': 'Casablanca',
    'adresse_agence': 'Angle rues Ifni et Rabia Al Adaouia, Casablanca 20500, Maroc'
}

MESSAGES = [
    {'id': '1', 'titre': 'Bienvenue sur votre espace', 'contenu': 'Nous sommes ravis de vous accueillir dans votre nouvel espace bancaire en ligne.', 'date': '2026-01-15', 'lu': False},
    {'id': '2', 'titre': 'Releve de janvier disponible', 'contenu': 'Votre releve de compte du mois de janvier est maintenant disponible.', 'date': '2026-01-14', 'lu': True},
    {'id': '3', 'titre': 'Nouveau taux epargne', 'contenu': 'Le taux du Livret A passe a 3% a compter du 1er fevrier.', 'date': '2026-01-10', 'lu': True},
]


# ======================
# ROUTES PAGES
# ======================
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        password = request.form.get('password')
        if identifiant == '990303' and password == '0275':
            session['user'] = USER
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Identifiant ou mot de passe incorrect')
    return render_template('login.html', error=None)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    total_epargne = sum(e['solde'] for e in EPARGNES)
    total_credits = sum(c['montant_restant'] for c in CREDITS)
    unread_count = sum(1 for m in MESSAGES if not m['lu'])
    return render_template('dashboard.html',
        user=user,
        transactions=TRANSACTIONS,
        ribs=RIBS,
        prelevements=PRELEVEMENTS,
        epargnes=EPARGNES,
        credits=CREDITS,
        assurances=ASSURANCES,
        services=SERVICES,
        domiciliation=DOMICILIATION,
        messages=MESSAGES,
        total_epargne=total_epargne,
        total_credits=total_credits,
        unread_count=unread_count
    )


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ======================
# ROUTES AJAX
# ======================
@app.route('/beneficiaire/add', methods=['POST'])
def add_beneficiaire():
    data = request.get_json()
    new_rib = {
        'id': str(len(RIBS) + 1),
        'prenom': data.get('prenom', ''),
        'nom': data.get('nom', ''),
        'iban': data.get('iban', ''),
        'bic': data.get('bic', ''),
        'adresse': data.get('adresse', '')
    }
    RIBS.append(new_rib)
    return jsonify({'success': True, 'message': 'Beneficiaire ajoute'})


@app.route('/beneficiaire/delete/<id>', methods=['POST'])
def delete_beneficiaire(id):
    global RIBS
    RIBS = [r for r in RIBS if r['id'] != id]
    return jsonify({'success': True, 'message': 'Beneficiaire supprime'})


@app.route('/virement', methods=['POST'])
def virement():
    data = request.get_json()
    montant = float(data.get('montant', 0))
    USER['solde'] -= montant
    session['user'] = USER
    ref = data.get('reference', '') or ('VIR-' + datetime.now().strftime('%Y%m%d%H%M%S'))
    TRANSACTIONS.insert(0, {
        'id': str(len(TRANSACTIONS) + 1),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'operation': 'Virement vers ' + data.get('prenom', '') + ' ' + data.get('nom', '') + ' - ' + data.get('motif', ''),
        'beneficiaire': data.get('prenom', '') + ' ' + data.get('nom', ''),
        'reference': ref,
        'montant': -montant,
        'type': 'debit'
    })

    # Envoi email de confirmation avec PDF
    email_dest = data.get('email', '')
    email_ok = False
    if email_dest:
        email_data = {
            'prenom': data.get('prenom', ''),
            'nom': data.get('nom', ''),
            'iban': data.get('iban', ''),
            'bic': data.get('bic', ''),
            'montant': montant,
            'reference': ref,
            'motif': data.get('motif', ''),
        }
        email_ok = envoyer_email_confirmation(email_dest, email_data)

    msg = 'Virement de ' + fmt_money(montant) + ' EUR effectue'
    if email_ok:
        msg = msg + '. Confirmation envoyee a ' + email_dest
    elif email_dest:
        msg = msg + '. Erreur envoi email.'

    return jsonify({'success': True, 'message': msg})


@app.route('/prelevement/toggle/<id>', methods=['POST'])
def toggle_prelevement(id):
    for p in PRELEVEMENTS:
        if p['id'] == id:
            if p['statut'] == 'actif':
                p['statut'] = 'suspendu'
            else:
                p['statut'] = 'actif'
            return jsonify({'success': True, 'statut': p['statut']})
    return jsonify({'success': False}), 404


@app.route('/service/demande', methods=['POST'])
def service_demande():
    data = request.get_json()
    SERVICES.insert(0, {
        'id': str(len(SERVICES) + 1),
        'type': data.get('type', ''),
        'date_demande': '2026-02-01',
        'statut': 'en_cours'
    })
    return jsonify({'success': True, 'message': 'Demande enregistree'})


@app.route('/message/read/<id>', methods=['POST'])
def mark_read(id):
    for m in MESSAGES:
        if m['id'] == id:
            m['lu'] = True
            return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/credit/simulation', methods=['POST'])
def credit_simulation():
    data = request.get_json()
    montant = float(data.get('montant', 0))
    duree = int(data.get('duree', 1))
    taux = float(data.get('taux', 3.5))
    taux_mensuel = taux / 100 / 12
    if taux_mensuel > 0:
        mensualite = montant * taux_mensuel / (1 - (1 + taux_mensuel) ** -duree)
    else:
        mensualite = montant / duree
    cout_total = mensualite * duree
    cout_credit = cout_total - montant
    return jsonify({
        'mensualite': round(mensualite, 2),
        'cout_total': round(cout_total, 2),
        'cout_credit': round(cout_credit, 2),
        'taux': taux
    })


# ======================
# LANCEMENT
# ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
