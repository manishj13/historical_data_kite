import time 
import requests
import datetime as dt
import pandas as pd
import streamlit as st
import base64
import json
import pickle
import uuid
import re


#Get input from user
global user_id,token,timeframe, ticker

# user_id = "VT5229"
# token = "sP0cU2koF6AntNHSuFXXUfXZXku+iwzc9IuVtLsXDXarCdEHHk9P0s9piz7q+tyLMCrH4yWvzPrqhHeeEwIKrgg88/N6Og=="
# timeframe = "minute"

#vlookup for instrument token
instruments = pd.read_csv("https://api.kite.trade/instruments/NSE")
data = instruments[['instrument_token','tradingsymbol']]
inst = data.set_index('tradingsymbol')
stocks = data['tradingsymbol'].to_list()


st.title("Historical Data -  Kite")

user_id = st.text_input('Enter your Kite ID:')
st.write("[Searching for enctoken - click here to find it](https://drive.google.com/file/d/10XpMhc5UN9LjFJPhWZmLHQdzjU302g6e/view?usp=sharing)")
token = st.text_input('Enter enctoken:')

#timeframe = st.selectbox('Enter the timeframe', ["minute","3minute","5minute","10minute","15minute","30minute","60minute"])
ticker = st.multiselect('Enter the TickerSymbol',stocks)


#Function to get last 60 days of data
def get_data(period, start_date,end_date,symbol):
    #scrip_ID = mapping.get(symbol)
    #user_id = 'VT5229'
    scrip_ID = inst.loc[symbol]['instrument_token']
    url = f"https://kite.zerodha.com/oms/instruments/historical/{scrip_ID}/{period}?user_id={user_id}&oi=1&from={start_date}&to={end_date}"
    
    #enctoken changes everytime you logoff
    #token = "sP0cU2koF6AntNHSuFXXUfXZXku+iwzc9IuVtLsXDXarCdEHHk9P0s9piz7q+tyLMCrH4yWvzPrqhHeeEwIKrgg88/N6Og=="
    
    payload={}
    headers = {
    'authority': 'kite.zerodha.com',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
    'accept': 'application/json, text/plain, */*',
    'authorization': f"enctoken {token}",
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://kite.zerodha.com/chart/web/tvc/INDICES/NIFTY%2050/256265',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '_ga=GA1.2.1237715775.1599025253; WZRK_G=35dc9bf39872453ca302ca61e69943d9; _hjid=a0fa20cf-2859-4186-addd-1ad51ce109c3; _fbp=fb.1.1599067875093.1182513860; mp_7b1e06d0192feeac86689b5599a4b024_mixpanel=%7B%22distinct_id%22%3A%20%225ef374f27072303def14c858%22%2C%22%24device_id%22%3A%20%221744fdf72e2277-05c84fb230310a-f7b1332-144000-1744fdf72e3148%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24user_id%22%3A%20%225ef374f27072303def14c858%22%2C%22__timers%22%3A%20%7B%7D%7D; __cfduid=d5db03e65a8d59b8756511c92cc839f141610687855; _gid=GA1.2.275777476.1611075594; kf_session=EQK5SCto80996B3JICoZQanok197GRGh; public_token=yu45f5lpkI9Oo2Ni91qJIMyzEv3GRh1N; user_id=VT5229; enctoken=x2FuRS3NQgllZxWymw/WjRNm+pxJbYsB+sPjTksKzwi+AwrBAGWZroZu5biMvrMe9BqZMLqxVn0NQ0q/sj6kBTTJb/bKxw=='
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    data = response.json()
    return data

#Function to scrap whole data at once
def scrap_data(scrip_name):
    
    scrip_name = str(scrip_name)
    df = pd.DataFrame(columns=['DateTime','Open','High','Low','Close','Volume'])
    
    final_start = "2015-01-01"
    start = dt.datetime.strptime(final_start,"%Y-%m-%d")
    end = start + dt.timedelta(60)
    
    diff = divmod((dt.datetime.today() - end).total_seconds(),86400)[0]
    
    while diff >= 0:
    
        start_date = dt.datetime.strftime(start,"%Y-%m-%d") 
        end_date = dt.datetime.strftime(end,"%Y-%m-%d")

        a = get_data('minute',start_date,end_date,scrip_name)['data']['candles']

        data = pd.DataFrame(a,columns = ['DateTime','Open','High','Low','Close','Volume','OI'])
        data.drop(columns=['OI'],inplace = True)

        df = df.append(data)

        diff = divmod((dt.datetime.today() - end).total_seconds(),86400)[0]

        if diff < 0:
            start = end + dt.timedelta(1)
            end = start + dt.timedelta(abs(diff))
        else:
            start = end + dt.timedelta(1)
            end = start + dt.timedelta(60)

    return df

#Function to transform data into new format
def transform(df):
    df.insert(1,'Date',0)
    df.insert(2,'Time',0)
    df[['Date','Time']] = df['DateTime'].str.split('T',expand = True)
    df[['Time','nan']] = df['Time'].str.split('+',expand = True)
    df.drop(['DateTime','nan'],axis = 1,inplace = True)
    
    return df



#Create list of stocks/index/option/future symbol that you want the data for
#stocks = ['INDIA VIX','SBIN']

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'

#download button
def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.

    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.

    Returns:
    -------
    (str): the anchor tag to download object_to_download

    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')

    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None
    
    else:
        if isinstance(object_to_download, bytes):
            pass
        
        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)
        
        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)
    
    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()
    
    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()
    
    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    prim_color = st.config.get_option('theme.primaryColor') or '#F43365'
    bg_color = st.config.get_option('theme.backgroundColor') or '#808080'
    sbg_color = st.config.get_option('theme.secondaryBackgroundColor') or '#f1f3f6'
    txt_color = st.config.get_option('theme.textColor') or '#00FF00' 
    font = st.config.get_option('theme.font') or 'sans serif'  


    custom_css = f"""
        <style>
            #{button_id} {{
                background-color: {bg_color};
                color: {txt_color};
                padding: 0.25rem 0.75rem;
                position: relative;
                line-height: 1.6;
                border-radius: 0.25rem;
                border-width: 1px;
                border-style: solid;
                border-color: {bg_color};
                border-image: initial;
                filter: brightness(105%);
                justify-content: center;
                margin: 0px;
                width: auto;
                appearance: button;
                display: inline-flex;
                family-font: {font};
                font-weight: 400;
                letter-spacing: normal;
                word-spacing: normal;
                text-align: center;
                text-rendering: auto;
                text-transform: none;
                text-indent: 0px;
                text-shadow: none;
                text-decoration: none;
            }}
            #{button_id}:hover {{
                
                border-color: {prim_color};
                color: {prim_color};
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: {prim_color};
                color: {sbg_color};
                }}
        </style> """
    
    dl_link = custom_css + f'<a download="{download_filename}" class= "" id="{button_id}" ' \
                           f'href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'
    
    return dl_link


#For a list of tickers

if st.button("Download Data"):
    for i in ticker:
        df = scrap_data(str(i))
        df.insert(0,'Ticker',i)
        df = transform(df)
        tmp_download_link = download_button(df, f'{i}.csv', button_text='Click here to download data for ' + i)
        st.markdown(tmp_download_link, unsafe_allow_html=True)
        #df.to_csv(i + '.csv')
        #st.write("Downloaded data for " + i)
        #st.markdown(get_table_download_link(df), unsafe_allow_html=True)
