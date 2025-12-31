import os
import re
import json
from pyrogram import Client
from colorama import Fore
import pyfiglet
import random
import sys

# Arquivo lista de contas
CREDENTIALS_FILE = "credentials.json"

def limpar_nome_arquivo(nome_arquivo):
    nome_limpo = re.sub(r'[^a-zA-Z0-9]', '_', nome_arquivo)
    chars_invalidos = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in chars_invalidos:
        nome_limpo = nome_limpo.replace(char, '_')
    return nome_limpo

class Banner:
    def __init__(self, banner):
        self.banner = banner
        self.lg = Fore.LIGHTGREEN_EX
        self.w = Fore.WHITE
        self.cy = Fore.CYAN
        self.ye = Fore.YELLOW
        self.r = Fore.RED
        self.n = Fore.RESET

    def print_banner(self):
        colors = [self.lg, self.r, self.w, self.cy, self.ye]
        f = pyfiglet.Figlet(font='slant')
        banner = f.renderText(self.banner)
        print(f'{random.choice(colors)}{banner}{self.n}')
        print(f'{self.r}  Version: v0.0.1 https://github.com/rtthush \n{self.n}')

def show_banner():
    banner = Banner('TG - Clone')
    banner.print_banner()

def cache_path():
    directories = ['downloads', 'download_tasks','forward_task','chat_download_task','sessions']

    for dir_name in directories:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

# --- GERENCIADOR DE CREDENCIAIS ---

def load_credentials_list():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("accounts", [])
        except:
            return []
    return []

def save_new_credential(api_id, api_hash, session_name, phone):
    accounts = load_credentials_list()
    
    # Verifica se já existe sessao com mesmo nome e remove para atualizar
    accounts = [acc for acc in accounts if acc['session_name'] != session_name]
    
    new_acc = {
        "session_name": session_name,
        "api_id": api_id,
        "api_hash": api_hash,
        "phone_label": phone
    }
    accounts.append(new_acc)
    
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump({"accounts": accounts}, f, indent=4)

def manage_credentials():
    """
    Controla o menu de escolha de contas.
    Retorna: (api_id, api_hash, session_name, phone)
    """
    accounts = load_credentials_list()
    
    print("\n--- GERENCIADOR DE CONTAS ---")
    if not accounts:
        print("Nenhuma conta salva encontrada.")
        choice = "1" # Força criação
    else:
        print("1 - Adicionar Nova Conta")
        print("2 - Usar Conta Salva")
        choice = input("Escolha uma opção: ").strip()

    if choice == "1":
        print("\n--- NOVA CONTA ---")
        print("Dica: Pegue as chaves em my.telegram.org")
        try:
            api_id = int(input("API_ID: ").strip())
        except ValueError:
            print("API_ID deve ser um número.")
            sys.exit(1)
            
        api_hash = input("API_HASH: ").strip()
        session_name = input("Nome para salvar esta sessão (ex: user1): ").strip()
        phone_input = input("Número do Telefone (com DDI, ex: +5511999999999): ").strip()

        phone = re.sub(r'[^0-9+]', '', phone_input)
        
        # Salva para o futuro
        save_new_credential(api_id, api_hash, session_name, phone)
        print("Conta salva com sucesso!")
        return api_id, api_hash, session_name, phone

    elif choice == "2":
        print("\n--- SELECIONE UMA CONTA ---")
        for idx, acc in enumerate(accounts):
            print(f"{idx + 1} - {acc.get('phone_label', 'Sem Numero')} [{acc['session_name']}]")
        
        try:
            sel = int(input("\nDigite o número da conta: ").strip())
            if 1 <= sel <= len(accounts):
                selected = accounts[sel - 1]

                raw_phone = selected.get('phone_label', '')
                clean_phone = re.sub(r'[^0-9+]', '', str(raw_phone))
                
                return selected['api_id'], selected['api_hash'], selected['session_name'], clean_phone
            else:
                print("Opção inválida.")
                sys.exit(1)
        except ValueError:
            print("Entrada inválida.")
            sys.exit(1)
    else:
        print("Opção inválida.")
        sys.exit(1)

def authenticate(session_name, api_id, api_hash, phone_number=None):
    """
    Autentica usando credenciais. Se phone_number for passado, 
    o Pyrogram não perguntará novamente.
    """

    # LIMPEZA DO NÚMERO: Remove espaços e traços para o Pyrogram aceitar
    if phone_number:
        phone_number = re.sub(r'[^0-9+]', '', str(phone_number))
    
    # if session file does not exists, obtain the credentials 
    if not os.path.exists(f"{session_name}.session"):
        print(f"\nIniciando primeiro login para '{session_name}'...")
        try:
            
            with Client(session_name, api_id=api_id, api_hash=api_hash, phone_number=phone_number) as app:
                print("Você está autenticado!")
        except Exception as e:
            print(f"Erro ao autenticar: {e}")
            sys.exit(1)
    else:
        print(f"Sessão '{session_name}' carregada com sucesso.")

def rename_files(directory, chat_title):
    
    chat_directory = os.path.join(directory, limpar_nome_arquivo(chat_title))
    files = [f for f in os.listdir(chat_directory) if os.path.isfile(os.path.join(chat_directory, f))]      
    files.sort(key=lambda x: os.path.getctime(os.path.join(chat_directory, x)))    
    for idx, filename in enumerate(files, start=1):
        # Substituir underscores por espaços
        cleaned_name = filename.replace("_", " ")
        new_name = f"{idx:03}_{cleaned_name}"
        os.rename(os.path.join(chat_directory, filename), os.path.join(chat_directory, new_name))
