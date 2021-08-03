# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# pour utiliser toute la largeur de la page
st.set_page_config(layout="wide")

# pour donner un titre à l'application
st.title('Solvabilité des clients')

# pour importer les données

path = 'predictions_solv.csv'

@st.cache # permet de ne pas relancer cette fonction à chaque relance de l'app
def load_data():
    ''' fonction qui importe les données nécessaires dans un DataFrame
    '''
    data = pd.read_csv(path)#, sep='\t')#, sep='delimiter', header=None)
    return data

# affichage d'un texte qui indique que les données sont en chargement
data_load_state = st.text('Chargement des données...')
# les données sont chargées dans le DataFrame data
data = load_data()
# Indique que les données sont chargées
data_load_state.text("Données chargées!") 

# création champ à remplir avec le numéro du client à étudier
ID_client_first = data.index.values.min()
ID_client_last = data.index.values.max()
text_box = 'Renseigner l\'ID du client à étudier (nombre entre ' + str(ID_client_first) + \
' et ' + str(ID_client_last) + ')'
st.subheader(text_box)
ID_client = st.number_input(label='', step=1, format='%d')

# création d'un DataFrame contenant les pourcentages de chances de remboursement
data_per = data['target'].copy()
data_per = 100 * data_per
data_per = pd.DataFrame({'target':data_per})

# création d'un slider (sur la solvablité) qui permet de filtrer les résultats
st.subheader(f'Seuil de tolérance (prédictions du % de chances que le prêt soit remboursé)')
threshold_per = st.slider(label="", min_value=0., max_value=100., value=50.)
filtered_data = data_per[data_per['target'] >= threshold_per]
threshold_solv = 0.01 * threshold_per # pour la colonne 'target' du dataset d'origine (entre 0 et 1)

# détermination du remboursement ou non du client choisi avec le seuil choisi
prob_solv = data['target'].iloc[ID_client]
if prob_solv >= threshold_solv:
    text_decision = 'Avec ce seuil de tolérance, le prêt du client choisi serait accordé'
    st.write(text_decision)
else:
    text_decision = 'Avec ce seuil de tolérance, le prêt du client choisi ne serait pas accordé'
    st.write(text_decision)
    

# calcul du nombre de prêts qui sont accordés avec le seuil choisi
num_solv = filtered_data.shape[0]
percent = 100 * num_solv / data.shape[0]
text_slider = 'Pour information, avec ce seuil il y aurait ' + str(num_solv) +\
' prêts accordés sur les demandes actuelles, soit ' + str("%.2f" % percent) + '% du total'
st.write(text_slider)

col1, col2 = st.beta_columns(2)

with col1:
    # menu déroulant pour choisir le paramètre à regarder plus en détail
    st.subheader('Choisir le paramètre à observer')
    list_columns = list(data.columns)
    list_columns.remove('target')
    list_binary = [elt for elt in list_columns if data[elt].unique().size<=2]
    column_chosen = st.selectbox(label='', options=list_columns)
    value_client = data[column_chosen].iloc[ID_client]
    st.write('Pour le client choisi ce paramètre vaut %.3f' % value_client)

    # bouton radio pour choisir le groupe représenté sur l'histogramme
    st.subheader('Sélectionner le groupe dont les données sont affichées')
    list_groups = ['Tous les clients', 'Les clients obtenant le prêt avec ce seuil',
    'Les clients n\'obtenant pas le prêt avec ce seuil']
    group = st.radio(label='', options=list_groups)
    
    # affichage de quelques données statistiques
    st.subheader('Statistiques du groupe choisi pour ' + column_chosen)
    if group == list_groups[0]: 
        arr = data[column_chosen]
    elif group == list_groups[1]:
        arr = data[data['target']>=threshold_solv][column_chosen]
    else:
        arr = data[data['target']<threshold_solv][column_chosen]
     
    if column_chosen in list_binary:
        per_same_client = 100 * arr[arr==value_client].size / arr.size
        st.write('Le client choisi a la même valeur que %.3f' % per_same_client + '% des clients de ce groupe')
    else:
        mean_gr = arr.mean()
        med_gr = arr.median()
        std_gr = arr.std()
        fig_st, ax_st = plt.subplots(figsize=(15,3))
        bars_st = [mean_gr, med_gr, std_gr]
        list_labels = ['moyenne', 'médiane', 'écart-type']
        ax_st.barh(y=[2,1,0], width=bars_st, height=0.5, tick_label=list_labels)
        ax_st.axvline(x=value_client, ymin=0, ymax=1, color='red')
        ax_st.tick_params(labelsize=20)
        ax_st.tick_params(axis='y', labelrotation=45)
        st.pyplot(fig_st)

with col2:
    # tracé de l'histogramme de la colonne choisie
    st.subheader('Histogramme (normalisé)')
        
    # bouton radio pour choisir l'échelle de l'histogramme
    list_scales = ['échelle linéaire (normale)', 'échelle logarithmique (écrasée)']
    scale = st.radio(label='', options=list_scales)
    
    if group == list_groups[0]: 
        arr = data[column_chosen]
    elif group == list_groups[1]:
        arr = data[data['target']>=threshold_solv][column_chosen]
    else:
        arr = data[data['target']<threshold_solv][column_chosen]
    
    min_col = data[column_chosen].min()
    max_col = data[column_chosen].max()
    if column_chosen in list_binary:
        min_col = min_col - 0.2 * (max_col-min_col)
        max_col = max_col + 0.2 * (max_col-min_col)

    fig, ax = plt.subplots()
    ax.set_title(column_chosen)
    nbins = 40
    x, bins, p = ax.hist(arr, bins=nbins, density=True)
    # pour normaliser les histogrammes
    for item in p:
        item.set_height(item.get_height()/sum(x))
    plot_label = 'client choisi'
    ax.axvline(x=value_client, ymin=0, ymax=1, color='red', label=plot_label)
    ax.set_xlim(xmin=min_col, xmax=max_col)
    ax.set_ylabel('part des clients')
    max_height = 1.2 * max(x) / sum(x)
    ax.legend()
    
    if scale == list_scales[0]:
        ax.set_ylim(ymin=0, ymax=max_height)
    else:
        min_value = 10**(-4) * max_height
        ax.set_ylim(ymin=min_value, ymax=max_height)
        ax.set_yscale('log')

    st.pyplot(fig)

st.subheader('Explication des prévisions')   
st.write('Les points bleus correspondent à des faibles valeurs du paramètre alors \
que les points rouges correspondent à des hautes valeurs. De plus, plus les points \
sont à gauche, plus cela signifie qu\'ils baissent la valeur (vers plus de solvabilité) \
et inversement')
st.write('Par exemple, un age élevé (points rouges de DAYS_BIRTH) va de paire avec une bonne \
solvabilité (point à gauche)')
image = Image.open('shapsummaryplot.png')   
st.image(image)