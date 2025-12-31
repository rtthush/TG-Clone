# TG CLONE

## Introdução

Um script que permite multiplas contas e multiplas clonagens para salvar seus conteúdos favoritos do Telegram. Versão atualizada do tg_mirror do viniped.

## Pré requisitos 

Python 3.13 - para instalar apenas abra o arquivo "instalar_python3.13_completo.bat"

ffmpeg - será instalado junto com as bibliotecas no arquivo "install_requirements.bat"

## Como instalar

**PASSO 1: INSTALAÇÃO (Faça apenas na primeira vez)**

Abra a pasta onde você extraiu os arquivos.

Abra o arquivo:

	instalar_python3.13_completo.bat

Uma janela preta vai abrir e instalar o sistema necessário. As variáveis de ambiente serão adicionadas automaticamente.

Agora, abra esse arquivo:

	install_requirements.bat

Ele vai baixar as bibliotecas do script incluindo o FFMpeg. Aguarde aparecer a mensagem de "Instalação concluída" e feche a janela.

Pronto! Está instalado.

## Primeiro acesso no script

- Abra o arquivo:

		exec-tg-clone.bat

**No primeiro acesso:**

Escolha a opção 1 (Adicionar Nova Conta).

O script vai pedir seu API ID e API HASH (chaves do Telegram). Para conseguir essas informações, acesse:

	https://my.telegram.org/apps

- Digite o nome da sessão (ex: minhaconta).

- Digite seu número de telefone com o código do país (Ex: +5511999999999).

O Telegram enviará um código para o seu telegram. Digite esse código no script.

## Como usar o script

Abra o arquivo:

	exec-tg-clone.bat

Selecione a opção que deseja:

	1 - Adicionar Nova Conta

	2 - Usar Conta Salva

Menu Principal: O script apresenta as seguintes opções:

	0 - Sair / Trocar Conta: Para logar com outro número.

	1 - Modo Manual: Você digita o Link ou ID do canal de origem.

	2 - Listar Meus Canais: Ele mostra os canais que você já participa (somente canais restritos, que não possuem encaminhamento ativo).

	3 - Retomar Clonagem: Use essa opção para continuar de onde parou.

Após selecionar um canal para clonar, escolha uma opção (o padrão é a opção 0 para processar todos os conteúdos):

	Quais conteudos você deseja processar?:

	0 - Processar todos os Conteúdos

	1 - Fotos
	
	2 - Áudios

	3 - Vídeos

	4 - Arquivos

	5 - Texto

	6 - Sticker

	7 - Animação - GIFs

## Como editar o arquivo config.json

Este arquivo controla como o script se comporta (velocidade, nomes e pausas). Para editar, clique com o botão direito no arquivo config.json e escolha "Abrir com Bloco de Notas".

**O que significa cada campo:**

- "channel_suffix":

		Padrão: " (BKP)"

		O que faz: É o texto que o script adiciona automaticamente ao final do nome do canal clonado.

		Exemplo: Se o canal original chama "Curso Python" e o sufixo é " (BKP)", o novo canal se chamará "Curso Python (BKP)".

- "max_concurrent_transmissions":

		Padrão: 2 (Recomendado: entre 2 e 5)

		O que faz: Define quantos arquivos o script baixa/envia ao mesmo tempo.

		Atenção: Aumentar muito consome muita internet e processador. Se seu PC for lento, deixe em 2. Se for rápido, pode tentar 5 ou 8.

- "max_retries":

		Padrão: 3

		O que faz: Quantas vezes o script vai tentar baixar um arquivo se der erro antes de desistir e pular para o próximo.

- "delay_between_files":

		Padrão: 10 (segundos)

		O que faz: Tempo de espera entre uma mensagem e outra.

		**Importante:** Se colocar 0, o Telegram pode bloquear sua conta temporariamente por "Flood" (envio rápido demais). Recomendamos deixar pelo menos 5 ou 10 segundos.

## Como editar o arquivo credentials.json

Embora o script tenha um menu para adicionar contas ("Opção 1"), você pode adicionar contas manualmente editando este arquivo.

Estrutura do arquivo: O arquivo deve conter uma lista de contas dentro de colchetes [ ].

Exemplo de como preencher:

```
JSON

{
    "accounts": [
        {
            "session_name": "minhaconta1",
            "api_id": 12345678,
            "api_hash": "a1b2c3d4e5f6g7h8i9j0",
            "phone_label": "+5511999999999"
        },
        {
            "session_name": "minhaconta2",
            "api_id": 87654321,
            "api_hash": "z9y8x7w6v5u4t3s2r1",
            "phone_label": "+5521988888888"
        }
    ]
}
```
Detalhes dos campos:

- session_name: É o nome do arquivo de sessão que será criado (sem espaços). Ex: pessoal, trabalho.

- api_id: O número de identificação da sua conta (pegar em my.telegram.org). Não use aspas aqui, pois é um número.

- api_hash: A chave secreta da sua conta (pegar em my.telegram.org). Use aspas.

- phone_label: Apenas para você identificar qual número é aquele no menu do script.

## Outras funções

Essas funções não foram modificadas (não foram testadas). São originais do tg_mirror.

	exec_download_module.bat : Executa o script que faz o download de todo o conteúdo de um canal seja protegido ou não.

	exec_forward_module.bat : Executa o script que faz o encaminhamento de um canal para um canal só seu criando assim uma cópia particular	
	
## Aviso Legal:

O script TG-CLONE é fornecido "como está" e sem garantias. É sua responsabilidade garantir que você tenha os direitos e permissões necessários para realizar as operações propostas. O autor do script não assume nenhuma responsabilidade por qualquer uso indevido ou danos causados pelo uso deste script.	 		
		
			

 

