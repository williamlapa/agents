import openai

# Configuração da chave da API (garanta que esteja configurada via variável de ambiente ou aqui)
# openai.api_key = 'SUA_CHAVE_AQUI'

# Exemplo Tool

def simular_pesquisa_web(query):
    """
    Simula uma busca na web e retorna conteúdo relevante com base na query.
    Em um cenário real, esta função faria uma requisição a uma API de busca.
    """
    print(f"\n[Ferramenta: Simular Pesquisa Web] Buscando por: '{query}'...")
    if "inteligencia artificial" in query.lower():
        return ("A Inteligência Artificial (IA) é um campo vasto da ciência da computação que busca criar máquinas capazes de raciocinar, aprender e agir de forma autônoma. "
                "Recentemente, modelos de linguagem grandes (LLMs) como GPT-4 e GPT-3.5-turbo revolucionaram a capacidade de IA em processamento de linguagem natural e geração de texto.")
    elif "energia solar no brasil" in query.lower():
        return ("A energia solar no Brasil tem crescido exponencialmente, impulsionada por incentivos governamentais e pela abundância de irradiação solar. "
                "Em 2024, a capacidade instalada de energia solar fotovoltaica ultrapassou marcos importantes, tornando-se uma das principais fontes da matriz energética do país.")
    else:
        return "Nenhum resultado relevante encontrado para esta query na nossa simulação."

## Exemplo de Agente Principal

def agente_pesquisador_e_sumarizador(topico_de_interesse):
    print(f"[Agente Principal] Tarefa recebida: Pesquisar e resumir sobre '{topico_de_interesse}'.")

    # Passo 1: O Agente decide usar a 'ferramenta_simular_pesquisa_web'
    print("[Agente Principal] Usando a ferramenta 'simular_pesquisa_web' para coletar dados...")
    informacao_coletada = simular_pesquisa_web(topico_de_interesse)

    if "Nenhum resultado" in informacao_coletada:
        print("[Agente Principal] Não foi possível coletar informações relevantes. Encerrando.")
        return "Não foi possível gerar um resumo."

    print(f"\n[Agente Principal] Informação coletada (trecho): '{informacao_coletada[:150]}...'")

    # Passo 2: O Agente usa o LLM (OpenAI) para realizar a sumarização.
    # Aqui, o próprio modelo da OpenAI atua como uma capacidade de raciocínio e processamento do agente.
    print("[Agente Principal] Processando informação coletada para gerar um resumo conciso com OpenAI...")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini", # Ou "gpt-4o" para melhor desempenho
            messages=[
                {"role": "system", "content": "Você é um assistente útil focado em resumir textos de forma clara e concisa."},
                {"role": "user", "content": f"Por favor, resuma o seguinte texto em 2-3 frases:\n\n{informacao_coletada}"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        resumo_final = response.choices[0].message.content.strip()
        print(f"\n[Agente Principal] Resumo gerado: '{resumo_final}'")
        return resumo_final

    except openai.APIError as e:
        print(f"[Agente Principal] Erro ao comunicar com a API da OpenAI: {e}")
        return "Ocorreu um erro ao gerar o resumo."
    
## Exemplo de handoffs

# --- Simulação do Fluxo Completo com Handoff ---

print("--- INÍCIO DO PROCESSO DE GERAÇÃO DE INFORMAÇÕES ---")

# Cenário 1: Pesquisar e Sumarizar sobre Inteligência Artificial
topico1 = "inteligencia artificial"
resumo_ia = agente_pesquisador_e_sumarizador(topico1)

print("\n---------------------------------------------------")
print(f"**CONCEITUAL HANDOFF:** O resumo de '{topico1}' agora está pronto para ser utilizado por outro sistema ou exibido ao usuário.")
print(f"Resumo Final Disponível: {resumo_ia}")
print("---------------------------------------------------\n")

# Cenário 2: Pesquisar e Sumarizar sobre Energia Solar no Brasil
topico2 = "energia solar no brasil"
resumo_energia = agente_pesquisador_e_sumarizador(topico2)

print("\n---------------------------------------------------")
print(f"**CONCEITUAL HANDOFF:** O resumo de '{topico2}' agora está pronto para ser utilizado por outro sistema ou exibido ao usuário.")
print(f"Resumo Final Disponível: {resumo_energia}")
print("---------------------------------------------------\n")

print("--- PROCESSO CONCLUÍDO ---")