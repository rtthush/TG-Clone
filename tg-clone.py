import os
import time
import json
import asyncio
import logging
from pyrogram import Client
from pyrogram.errors import PeerIdInvalid, RPCError
from pathlib import Path
import subprocess
import pyrogram.utils
from tqdm import tqdm
from utils import Banner, show_banner, cache_path, authenticate, manage_credentials
import re
import pyrogram
import sys

pyrogram.utils.MIN_CHANNEL_ID = -1002999999999

""" Global """
video_path = 'downloads'
sessao_arquivo = ""

# Variáveis globais de credenciais para permitir troca
current_api_id = None
current_api_hash = None
current_session_name = None
current_phone = None

# --- NOVA CLASSE DE EXCEÇÃO PARA VOLTAR AO MENU ---
class RestartScript(Exception):
    """Exceção levantada para reiniciar o fluxo do script (Voltar ao Menu)."""
    pass

# --- NOVA FUNÇÃO DE INPUT INTELIGENTE ---
def input_smart(prompt_text):
    """
    Substitui o input() padrão.
    Se o usuário digitar 'menu', levanta RestartScript.
    Caso contrário, retorna o valor digitado.
    """
    valor = input(prompt_text)
    if valor.strip().lower() == "menu":
        raise RestartScript("Voltando ao menu principal...")
    return valor
# ----------------------------------------

# --- CARREGAMENTO DE CONFIGURAÇÕES (config.json) ---
# Valores padrão
config_data = {
    "channel_suffix": " (BKP)",
    "performance": {
        "max_concurrent_transmissions": 2,
        "max_retries": 3,
        "delay_between_files": 10
    }
}

# Tenta ler o arquivo externo
if os.path.exists("config.json"):
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            arquivo_config = json.load(f)
            config_data.update(arquivo_config)
            print("Configurações carregadas do arquivo config.json com sucesso.")
    except Exception as e:
        print(f"Erro ao ler config.json: {e}. Usando valores padrão.")

# Aplica as configurações
CHANNEL_SUFFIX = config_data.get("channel_suffix", " (BKP)")
perf = config_data.get("performance", {})
MAX_CONCURRENT_TRANSMISSIONS = perf.get("max_concurrent_transmissions", 2)
MAX_RETRIES = perf.get("max_retries", 3)
DELAY_BETWEEN_FILES = perf.get("delay_between_files", 10)
# ---------------------------------------------------


def limpar_nome_arquivo(nome_arquivo):
    if not nome_arquivo:
        return "arquivo_sem_nome"
    
    # 1. Caracteres proibidos no Windows: < > : " / \ | ? *
    # Remove apenas esses. O resto (acentos, espaços) fica.
    chars_proibidos = r'[<>:"/\\|?*]'
    
    # Substitui os proibidos por nada (apaga) ou por _ se preferir
    nome_limpo = re.sub(chars_proibidos, '', nome_arquivo)
    
    # 2. Remove caracteres de controle (quebras de linha, tabs invisíveis que as vezes vem do Telegram)
    nome_limpo = "".join(ch for ch in nome_limpo if ord(ch) >= 32)
    
    # 3. Remove espaços duplicados e espaços no começo/fim
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo).strip()
    
    # 4. Garante que o nome não ficou vazio depois da limpeza
    if not nome_limpo:
        return "arquivo_renomeado"
        
    return nome_limpo

def get_cleaned_file_path(media, directory):
    extension = media.file_name.split('.')[-1] if media.file_name and '.' in media.file_name else 'unknown'
    clean_name = limpar_nome_arquivo(media.file_name or f"{media.file_id}.{extension}")
    return os.path.join(directory, clean_name)

def get_channels():
    """
    Função modificada para incluir Auto-Clone e Resume Multi-Sessão e LISTAGEM INTELIGENTE
    """
    # Precisamos da global para definir qual arquivo de sessão será usado/apagado no final
    global sessao_arquivo, current_api_id, current_api_hash, current_session_name, current_phone

    # Garante que a pasta de sessões existe
    if not os.path.exists('sessions'):
        os.makedirs('sessions')
    
    with Client(current_session_name, api_id=current_api_id, api_hash=current_api_hash, phone_number=current_phone) as client:

        # --- MENU DE SELEÇÃO ---
        print("\n=== MENU PRINCIPAL ===")
        print("0 - Sair / Trocar Conta")
        print("1 - Digitar ID ou Link manualmente")
        print("2 - Listar meus canais (Apenas Restritos e Pendentes)")
        print("3 - Retomar clonagem anterior (Backups Pausados)")
        
        # Uso do input_smart para permitir 'menu'
        modo_selecao = input_smart("Escolha (0, 1, 2 ou 3): ").strip()

        if modo_selecao == '0':
            # Força o reinício total para trocar credenciais
            # Limpa as variáveis globais atuais

            try:
                client.stop()
            except:
                pass

            current_api_id = None
            raise RestartScript("Trocando de conta...")
        
        chat_info = None

        # --- OPÇÃO 3: RETOMAR BACKUP ---
        if modo_selecao == '3':

            # Cria uma lista com os IDs de todos os canais que a conta atual participa
            meus_canais_ids = set()
            try:
                for dialog in client.get_dialogs():
                    meus_canais_ids.add(dialog.chat.id)
            except Exception as e:
                print(f"Erro ao validar permissões da conta: {e}")
            # -------------------------------------
            
            print("\nBuscando backups em andamento...")
            backups_encontrados = []
            
            # Varre a pasta sessions em busca de JSONs
            for filename in os.listdir('sessions'):
                if filename.endswith(".json"):
                    filepath = os.path.join('sessions', filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            
                            # Tenta descobrir o progresso lendo o log de download correspondente
                            s_id = data.get('source_id')
                            t_id = data.get('target_id')
                            title = data.get('source_title')

                            # --- FILTRO DE SEGURANÇA ---
                            # Se o ID do canal de origem não estiver na lista de canais da conta atual,
                            # pula este arquivo e não exibe no menu.
                            if s_id not in meus_canais_ids:
                                continue
                            # ---------------------------
                            
                            # Reconstrói o nome do log para ler a última mensagem processada
                            log_file = get_json_filepath(s_id, t_id, title)
                            last_msg = 0
                            if os.path.exists(log_file):
                                with open(log_file, 'r') as lf:
                                    ldata = json.load(lf)
                                    last_msg = ldata.get("last_processed_id", 0)
                            
                            backups_encontrados.append({
                                "filepath": filepath,
                                "data": data,
                                "last_msg": last_msg
                            })
                    except: continue

            if not backups_encontrados:
                print("Nenhum backup compatível com esta conta encontrado.")
                print("Nota: Backups de canais que você não participa foram ocultados.")
                print("Retornando ao Menu Principal...")
                raise RestartScript("Voltando ao menu...")
                modo_selecao = '1'
            else:
                print(f"\n--- BACKUPS PAUSADOS ({len(backups_encontrados)}) ---")
                for i, bkp in enumerate(backups_encontrados):
                    d = bkp['data']
                    print(f"{i + 1} - {d.get('source_title')} (Parou na msg {bkp['last_msg']})")
                
                try:
                    escolha_str = input_smart("\nDigite o NÚMERO do backup para retomar: ").strip()
                    escolha = int(escolha_str)
                    
                    if 1 <= escolha <= len(backups_encontrados):
                        selecionado = backups_encontrados[escolha - 1]
                        dados = selecionado['data']
                        
                        # ATUALIZA O ARQUIVO DE SESSÃO ATUAL PARA O QUE FOI ESCOLHIDO
                        sessao_arquivo = selecionado['filepath']
                        print(f"   Origem: {dados.get('source_title', 'Desconhecido')}")
                        print(f"   Destino (BKP): {dados.get('target_title', 'Desconhecido')}")
                        
                        return dados['source_id'], dados['target_id'], dados['source_title']
                    else:
                        print("Número inválido.")
                        raise RestartScript("Número inválido.")
                except ValueError:
                    print("Entrada inválida.")
                    raise RestartScript("Entrada inválida.")

        # --- OPÇÃO 2: LISTAR CANAIS ---
        if modo_selecao == '2':
            print("\nCarregando e filtrando canais (aguarde)...")
            canais_restritos = []


            
            # --- FILTRAGEM DE BACKUPS EXISTENTES ---
            all_dialogs = list(client.get_dialogs())
            
            # 1. Identificar nomes de canais que já possuem Backup
            # Ex: Se existe "Curso A (BKP)", adicionamos "Curso A" na lista de ignorados.
            nomes_com_backup = set()
            for d in all_dialogs:
                if d.chat.title and d.chat.title.endswith(CHANNEL_SUFFIX):
                    # Remove o sufixo para pegar o nome original
                    nome_original = d.chat.title.replace(CHANNEL_SUFFIX, "").strip()
                    nomes_com_backup.add(nome_original)

            # 2. Filtrar a lista
            for dialog in all_dialogs:
                try:
                    chat = dialog.chat
                    
                    # Regra A: Tem que ter conteúdo protegido
                    if not getattr(chat, "has_protected_content", False): 
                        continue
                    
                    # Regra B: Não listar o próprio canal de Backup (não fazer backup do backup)
                    if chat.title and chat.title.endswith(CHANNEL_SUFFIX):
                        continue

                    # Regra C: Não listar se já existe um backup dele
                    if chat.title in nomes_com_backup:
                        continue
                    
                    canais_restritos.append(chat)
                except:
                    continue
            # ----------------------------------------
            
            if not canais_restritos:
                print("Nenhum canal restrito encontrado na sua conta.")
                print("Dica: Canais que já possuem backup (BKP) foram ocultados.")
                print("Retornando ao Menu Principal...")
                raise RestartScript("Voltando ao menu...")
            else:
                print(f"\n--- CANAIS RESTRITOS PARA CLONAGEM ENCONTRADOS ({len(canais_restritos)}) ---")
                for i, chat in enumerate(canais_restritos):
                    print(f"{i + 1} - {chat.title}")
                
                try:
                    escolha_str = input_smart("\nDigite o NÚMERO do canal desejado: ").strip()
                    escolha = int(escolha_str)
                    
                    if 1 <= escolha <= len(canais_restritos):
                        chat_info = canais_restritos[escolha - 1]
                        print(f"Canal selecionado: {chat_info.title}")
                    else:
                        print("Número inválido.")
                        raise RestartScript("Número inválido.")
                except ValueError:
                    print("Entrada inválida.")
                    raise RestartScript("Entrada inválida.")

        # Se escolheu modo 1 OU se o modo 2 não achou nada
        if chat_info is None:
            
            # 2. Fluxo de Criação Automática
            if modo_selecao == '2' or modo_selecao == '3':
                # Se caiu aqui, é porque algo falhou nas opções anteriores
                pass
            
            channel_source_input = input_smart("\nForneça o @username ou ID do canal / grupo de ORIGEM: ")
            channel_source = parse_channel_input(channel_source_input)
            
            print("Buscando informações do canal...")
            try:
                chat_info = client.get_chat(channel_source)
                print(f"Origem localizada: {chat_info.title}")
            except Exception as e:
                print(f"Erro ao acessar canal de origem: {e}")
                raise RestartScript("Erro ao acessar canal.")

        # 3. Cria canal de destino automaticamente
        novo_titulo = f"{chat_info.title}{CHANNEL_SUFFIX}"
        print(f"Criando canal de destino: '{novo_titulo}'...")
        
        try:
            # Cria o canal e salva o ID na variável 'channel_target'
            target_info = client.create_channel(
                title=novo_titulo, 
                description=f"Backup de {chat_info.title}"
            )
            channel_target = target_info.id
            print(f"Canal criado! ID: {channel_target}")
        except Exception as e:
            print(f"Erro ao criar canal: {e}")
            raise RestartScript("Erro ao criar canal.")

        # 4. Clona Foto
        if chat_info.photo:
            print("Copiando foto de perfil...")
            try:
                p_path = client.download_media(chat_info.photo.big_file_id)
                client.set_chat_photo(channel_target, photo=p_path)
                os.remove(p_path)
            except: pass

        # 5. Salva sessão NA PASTA SESSIONS
        # Usamos o ID do canal como nome do arquivo para ser único
        sessao_arquivo = os.path.join('sessions', f"{chat_info.id}.json")
        
        dados_sessao = {
            "source_id": chat_info.id,
            "target_id": channel_target,
            "source_title": chat_info.title,
            "target_title": novo_titulo
        }
        with open(sessao_arquivo, "w") as f:
            json.dump(dados_sessao, f)

        # Atualiza channel_source para o ID numérico garantido
        channel_source = chat_info.id

        return channel_source, channel_target, chat_info.title

def parse_channel_input(channel_input: str):
    """Parse channel input to determine if it's an ID or username."""
    if channel_input.startswith("@"):
        return channel_input
    else:
        try:
            return int(channel_input)
        except ValueError:
            print("Entrada inválida.")
            raise RestartScript("ID inválido.")

def get_user_choices():
    print("\nQuais conteudos você deseja processar?:\n")
    options = ["Processar todos os Conteúdos", "Fotos", "Áudios", "Vídeos", "Arquivos", "Texto", "Sticker", "Animação - GIFs"]
    for i, option in enumerate(options):
        print(f"{i} - {option}")

    choices_str = input_smart("\nInforme os conteúdos que deseja procesar separados por vírgula (ex: 1,3) < 0 para processar todos ou 'menu': ")
    choices = choices_str.split(',')

    if len(choices) == 1 and choices[0] == '':
        return [1, 2, 3, 4, 5, 6, 7]

    try:
        choices = [int(choice.strip()) for choice in choices]
    except:
        return [1, 2, 3, 4, 5, 6, 7]

    if 0 in choices:
        choices = [1, 2, 3, 4, 5, 6, 7]
    return choices

def extract_thumbnail(video_path: str) -> str:
    thumbnail_path = video_path + ".jpg"

    # Extract frame from 00:00:01
    thumbnail_command = [
        'ffmpeg',
        '-v', 'quiet',    
        '-nostats',        
        '-y',
        '-i', video_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        thumbnail_path
    ]
    try:
        subprocess.run(thumbnail_command)
        return thumbnail_path
    except Exception as e:
        print(f"Erro ao extrair miniatura: {e}")
        return ""

def collect_video_duration(video_path: str) -> int:
    try:
        ffprobe_command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        duration = subprocess.check_output(ffprobe_command).decode('utf-8').strip()
        return int(float(duration))
    except Exception as e:
        print(f"Erro ao coletar duração do vídeo: {e}")
        return 0

def clean_filename(filename):
    unsupported_chars = '<>:"/\\|?#{}[]*'  
    for char in unsupported_chars:
        filename = filename.replace(char, '_')
    filename = filename.strip().strip('.')
    return filename    

def get_json_filepath(channel_source, channel_target, chat_title):
    filename = f"downloaded_media_{chat_title}_{channel_source}_{channel_target}.json"
    cleaned_filename = clean_filename(filename)
    return os.path.join('download_tasks', cleaned_filename)

async def download_and_upload_media_from_channel(choices, channel_source, channel_target, chat_title):
    downloaded_media = []
    last_processed_id = 0
    json_filepath = get_json_filepath(channel_source, channel_target, chat_title)

    # Cria diretório de downloads se não existir
    if not os.path.exists(video_path):
        os.makedirs(video_path)

    if os.path.exists(json_filepath):
        with open(json_filepath, "r") as json_file:
            data = json.load(json_file)
            last_processed_id = data.get("last_processed_id", 0)
            print(f"\nRetomando da MSG: {last_processed_id + 1}")

    # --- CLASSE AUXILIAR PARA VELOCIDADE ---
    class ProgressTracker:
        def __init__(self):
            self.start_time = time.time()
            self.last_time = time.time()
            self.last_bytes = 0
            self.speed_mbps = 0.0
            self.finished = False # Nova trava para garantir a quebra de linha

        def update(self, current, total, op_type, attempt_num):

            if self.finished:
                return
            
            now = time.time()
            dt = now - self.last_time
            
            # Atualiza o cálculo a cada 0.5 segundos para não piscar muito
            if dt >= 0.5 or current == total:
                diff_bytes = current - self.last_bytes
                if dt > 0:
                    # Cálculo: (Bytes * 8 bits) / (1 milhão * tempo)
                    speed_bps = diff_bytes / dt
                    self.speed_mbps = (speed_bps * 8) / 1_000_000
                
                self.last_time = now
                self.last_bytes = current

            percent = current * 100 / total

            # --- Cálculo de MB ---
            current_mb = current / 1048576  # 1024*1024
            total_mb = total / 1048576
            # ---------------------------
                        
            status_line = f"\r{op_type} (Tentativa {attempt_num}): {percent:.1f}% - Velocidade: {self.speed_mbps:.2f} Mbps - {current_mb:.1f}MB / {total_mb:.1f}MB   \033[K"

            if current == total:
                # Se chegou em 100%, imprime normal (sem end="") para pular linha e fixar o texto
                print(status_line) 
                self.finished = True
            else:
                # Se ainda está baixando, usa end="" para manter na mesma linha
                print(status_line, end="")
    # ---------------------------------------


    async with Client(current_session_name, api_id=current_api_id, api_hash=current_api_hash, phone_number=current_phone, max_concurrent_transmissions=MAX_CONCURRENT_TRANSMISSIONS) as client:
        # --- VALIDAÇÃO DE CANAL ---
        print("Sincronizando chats para validar o ID de destino")
        target_found = False

        # Isso força o script a baixar a lista dos seus canais e salvar os 'access_hashs'
        async for dialog in client.get_dialogs():
            if dialog.chat.id == channel_target:
                target_found = True
                print(f"Canal de destino confirmado: {dialog.chat.title}")
                break
        if not target_found:
            print(f"AVISO: Canal ID: {channel_target} não encontrado na lista.")
        # ---------------------------

        all_messages = []
        async for msg in client.get_chat_history(channel_source):
            all_messages.append(msg)
        all_messages.reverse()
        
        start_processing = False

        for count, message_old in enumerate(all_messages):
            if start_processing or message_old.id > last_processed_id:
                start_processing = True
            else:
                continue

            # --- INICIO DO SISTEMA DE TENTATIVAS (RETRY) ---
            attempt = 0
            success = False
            
            while attempt < MAX_RETRIES:
                file_name = None
                thumb_path = None
                
                try:
                    # 1. Refresh da mensagem (Evita FileReferenceExpired)
                    try:
                        message = await client.get_messages(channel_source, message_old.id)
                        if not message or message.empty:
                            print(f"Mensagem {message_old.id} não existe mais.")
                            success = True # Consideramos sucesso para pular e não travar
                            break 
                    except Exception as e:
                        print(f"Erro ao atualizar mensagem {message_old.id}: {e}")
                        raise e # Força cair no except principal para tentar de novo

                    caption_text = message.caption or ""
                    duration = 0

                    # Identifica o tipo de mídia
                    media_obj = None
                    type_str = ""

                    if 1 in choices and message.photo:
                        media_obj = message.photo
                        type_str = "photo"
                    elif 2 in choices and message.audio:
                        media_obj = message.audio
                        type_str = "audio"
                    elif 3 in choices and message.video:
                        media_obj = message.video
                        type_str = "video"
                    elif 4 in choices and message.document:
                        media_obj = message.document
                        type_str = "document"
                    elif 6 in choices and message.sticker:
                        media_obj = message.sticker
                        type_str = "sticker"
                    elif 7 in choices and message.animation:
                        media_obj = message.animation
                        type_str = "animation"
                    elif 5 in choices and message.text:
                        await client.send_message(channel_target, message.text)
                        success = True
                        break # Sai do while de tentativas

                    # Se não tiver mídia (e não for texto), consideramos processado
                    if not media_obj:
                        success = True
                        break

                    # 2. Preparar nome e Caminho
                    
                    original_name = getattr(media_obj, 'file_name', f"{message.id}_{type_str}")
                    if not original_name: original_name = f"{message.id}_{type_str}"
                    clean_name = limpar_nome_arquivo(original_name)
                    
                    if "." not in clean_name:
                         ext = "jpg" if type_str == "photo" else "mp4" if type_str in ["video", "animation"] else "Unknown"
                         clean_name = f"{clean_name}.{ext}"

                    file_name = os.path.join(video_path, clean_name)

                    # 3. Download
                    
                    print(f"\n") # Pula linha para separar do arquivo anterior
                    
                    # Reseta o rastreador de velocidade para o download
                    dl_tracker = ProgressTracker()

                    msg_label_dl = f"Baixando msg {message.id}"

                    try:
                        dl_path = await client.download_media(
                            message, 
                            file_name=file_name, 
                            progress=lambda c, t: dl_tracker.update(c, t, msg_label_dl, attempt + 1)
                        )
                    except asyncio.CancelledError:
                        raise
                    
                    # 4. Upload
                    
                    # Reseta o rastreador de velocidade para o upload
                    up_tracker = ProgressTracker()

                    msg_label_up = f"Enviando msg {message.id}"

                    if type_str == "video":
                        duration = collect_video_duration(dl_path)
                        thumb_path = extract_thumbnail(dl_path)
                        
                        kwargs = {
                            "caption": caption_text, "duration": duration, 
                            "progress": lambda c, t: up_tracker.update(c, t, msg_label_up, attempt + 1)
                        }
                        if thumb_path and os.path.exists(thumb_path): kwargs["thumb"] = thumb_path
                        
                        await client.send_video(channel_target, dl_path, **kwargs)
                        
                    elif type_str == "photo":
                        await client.send_photo(channel_target, dl_path, caption=caption_text)
                    elif type_str == "audio":
                        await client.send_audio(channel_target, dl_path, caption=caption_text)
                    elif type_str == "document":
                        await client.send_document(channel_target, dl_path, caption=caption_text)
                    elif type_str == "sticker":
                        await client.send_sticker(channel_target, dl_path)
                    elif type_str == "animation":
                        await client.send_animation(channel_target, dl_path)

                    # Se chegou aqui, deu tudo certo
                    success = True
                    break # Sai do loop de tentativas

                except asyncio.CancelledError:
                    # Se foi cancelado (CTRL+C) durante o download/upload
                    print("\nOperação cancelada pelo usuário durante a transmissão.")
                    # Limpeza de emergência
                    if file_name and os.path.exists(file_name):
                        try: os.remove(file_name)
                        except: pass
                    raise # Repassa o erro para encerrar a função async graciosamente

                except Exception as e:
                    attempt += 1
                    print(f"\n ERRO na tentativa {attempt}: {e}")
                    await asyncio.sleep(10) # Espera um pouco antes de tentar de novo


                finally:
                    # Tenta limpar o arquivo principal
                    if file_name and os.path.exists(file_name):
                        for i in range(3): # Tenta 3 vezes
                            try:
                                os.remove(file_name)
                                break # Se conseguiu, sai do loop
                            except PermissionError:
                                # Se deu erro de permissão (arquivo em uso), espera um pouco
                                print(f"Aguardando permissão")
                                await asyncio.sleep(1)
                            except Exception as e:
                                print(f"\nErro ao deletar arquivo: {e}")
                                break

                    # Tenta limpar a miniatura (thumbnail)
                    if thumb_path and os.path.exists(thumb_path):
                        try:
                            os.remove(thumb_path)
                        except:
                            pass

            if success:
                # Só salva o checkpoint se teve sucesso
                with open(json_filepath, "w") as json_file:
                    json.dump({"last_processed_id": message_old.id}, json_file)
                print(f"Mensagem {message_old.id} FINALIZADA com sucesso.")
                await asyncio.sleep(DELAY_BETWEEN_FILES)
            else:
                # Se saiu do while sem sucesso (attempt == MAX_RETRIES)
                print(f"\nFALHA CRÍTICA na mensagem {message_old.id} após {MAX_RETRIES} tentativas.")
                # Em vez de sys.exit, levantamos exceção para voltar ao menu
                raise RestartScript("Falha crítica na mensagem.")

    print("Todas as tarefas foram concluídas!")
    # Limpa arquivo de sessão específico da pasta sessions ao terminar tudo
    if sessao_arquivo and os.path.exists(sessao_arquivo):
        os.remove(sessao_arquivo)

if __name__ == "__main__":
    show_banner()

    # --- SILENCIAR MENSAGENS DE ERRO DO ASYNCIO (TASK DESTROYED) ---
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    # ---------------------------------------------------------------
    
    cache_path()

    while True:

        asyncio.set_event_loop(asyncio.new_event_loop())
        
        try:
            print("\n" + "="*40)

            # Se não tem credenciais carregadas, pede para carregar (ou recarregar)
            if not current_api_id:
                current_api_id, current_api_hash, current_session_name, current_phone = manage_credentials()
                time.sleep(1)

            # Executa o fluxo principal
            channel_source, channel_target, chat_title = get_channels()
            time.sleep(1)
    
            choices = get_user_choices()
    
            try:
                # Executa a clonagem
                asyncio.run(download_and_upload_media_from_channel(choices, channel_source, channel_target, chat_title))
                print("\nCiclo finalizado. Retornando ao Menu Principal...")
            
            except KeyboardInterrupt:
                # Captura Ctrl+C DURANTE a clonagem (barra de progresso)
                print("\n\n[!] Interrupção detectada (Ctrl+C). Parando downloads...")
                print("Voltando ao Menu Principal em 2 segundos...")
                time.sleep(2)
                # O loop continua automaticamente
            
        except RestartScript as e:
            # Captura o comando 'menu' digitado ou erros forçados para reiniciar
            print(f"\n[!] {e}")
            
            if "Trocando de conta" in str(e):
                print("Retornando ao Gerenciador de Contas...")
            else:
                print("Retornando ao Menu Principal...")
                
            time.sleep(1)
            # Limpa variáveis de sessão para evitar poluição no próximo ciclo
            sessao_arquivo = ""
            channel_source = None
            channel_target = None
            chat_title = None
            continue # Volta para o topo do while True
            
        except KeyboardInterrupt:
            # Captura Ctrl+C nos menus (fora da clonagem) para sair do programa de vez se o usuário insistir
            print("\nSaindo do programa...")
            sys.exit(0)
            
        except Exception as e:
            print(f"\n[ERRO INESPERADO]: {e}")
            print("Tentando recuperar e voltar ao menu...")
            time.sleep(3)
