#Importando pacotes necessários
import requests
import pandas as pd
from groq import Groq
import os
import re
from dotenv import load_dotenv
import boto3

load_dotenv()

#Gerando client key do Reddit
SUBREDDIT = 'politics'
client_id = os.environ.get('REDDIT_CLIENT_ID')
client_secret = os.environ.get('REDDIT_CLIENT_KEY')
user_agent = os.environ.get('REDDIT_USER_AGENT')


#Create an S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
)
CSV_PATH = f'{SUBREDDIT}.csv'




# Obtendo acess token
def obter_reddit_acess_token(client_id, client_secret):
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": user_agent}

    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers)
    token = response.json()["access_token"]
    return token

# Pegando hot pots de um subreddit
def get_hot_posts(subreddit, token):
    posts_requests = requests.get(
        f"https://oauth.reddit.com/r/politics/hot",
        headers={
            "User-Agent": user_agent,
            "Authorization": f"bearer { token}"
        }
    )
    return posts_requests.json()

#Criando dataframe com os posts capturados no Reddit
def create_post_df(posts):
    posts_data = []

    for post in posts["data"]["children"]:
        posts_data.append({
            "id": posts["kind"] + "_" + post["data"]["id"],
            "subreddit": post["data"]["subreddit"],
            "kind": post["kind"],
            "title": post["data"]["title"],
            "score": post["data"]["score"],
            "selftext": post["data"]["selftext"]
        })

    return pd.DataFrame(posts_data)


# Variaveis Deep Seek
os.environ["GROQ_API_KEY"] = os.environ.get('GROQ_API_KEY')
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


# Classificar o sentimento
def classificar_posicionamento(texto):
    resposta = client.chat.completions.create(
    
    messages=[
        {"role": "system",
          "content": "Você é um analista político econômico que possui conhecimento suficiente para calssificar posições político econômicas"
        },
        {"role": "user",
          "content": f"Classifique o viés político econômico do seguinte texto em 'Esquerda', 'Direita', 'Centro', retorne apenas uma string {texto}"
        },
    ],
    model="deepseek-r1-distill-llama-70b",
    stream=False
)
     # Extrai o conteúdo da resposta
    resposta_completa = resposta.choices[0].message.content
    
    # Remove tudo entre <think> e </think> usando expressão regular
    resposta_limpa = re.sub(r'<think>.*?</think>', '', resposta_completa, flags=re.DOTALL)
    
    
     # Remove espaços em branco extras e retorna a resposta limpa
    return resposta_limpa.strip()

# Juntando tudo
print('Obtendo Access Token')
token = obter_reddit_acess_token(client_id, client_secret)

print('Obtendo hot posts')
posts = get_hot_posts(SUBREDDIT, token)
df_posts = create_post_df(posts)
texto = ('Esquerda', "Direita", "Centro")

# Classificando o posicionamento dos posts
df_posts["posicionamento"] = df_posts["title"].apply(classificar_posicionamento)

print(f'Salvando {CSV_PATH}')
df_posts.to_csv(CSV_PATH, index = False)

#Escrevendo no S3
bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")
object_name = CSV_PATH
s3.upload_file(CSV_PATH, bucket_name, f'subreddits/{CSV_PATH}')