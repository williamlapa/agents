import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

def obter_saldo_openai(api_key, debug=False):
    """
    Obtém o saldo atual da conta OpenAI
    
    Args:
        api_key (str): Sua chave de API da OpenAI
        debug (bool): Se True, exibe informações de debug
    
    Returns:
        dict: Informações do saldo ou erro
    """
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Primeiro, vamos testar se a API key está válida
        test_url = 'https://api.openai.com/v1/models'
        test_response = requests.get(test_url, headers=headers)
        
        if debug:
            print(f"Teste de conectividade: {test_response.status_code}")
        
        if test_response.status_code != 200:
            error_detail = ""
            try:
                error_data = test_response.json()
                error_detail = error_data.get('error', {}).get('message', '')
            except:
                error_detail = test_response.text
                
            return {
                'status': 'erro',
                'codigo': test_response.status_code,
                'mensagem': f'API Key inválida ou problema de autenticação: {error_detail}'
            }
        
        # Tentar obter informações de billing/usage
        # Endpoint atualizado para billing
        from datetime import datetime, timedelta
        
        # Data de hoje e início do mês
        hoje = datetime.now()
        inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
        fim_mes = hoje.strftime('%Y-%m-%d')
        
        # URL para obter uso atual do mês
        usage_url = f'https://api.openai.com/v1/dashboard/billing/usage?start_date={inicio_mes}&end_date={fim_mes}'
        
        if debug:
            print(f"Consultando uso: {usage_url}")
            
        usage_response = requests.get(usage_url, headers=headers)
        
        if debug:
            print(f"Status uso: {usage_response.status_code}")
            
        # URL para obter subscription/limites
        subscription_url = 'https://api.openai.com/v1/dashboard/billing/subscription'
        subscription_response = requests.get(subscription_url, headers=headers)
        
        if debug:
            print(f"Status subscription: {subscription_response.status_code}")
        
        # Processar respostas
        uso_mensal = 0
        limite_credito = 0
        
        if usage_response.status_code == 200:
            usage_data = usage_response.json()
            uso_mensal = usage_data.get('total_usage', 0) / 100  # Converter centavos para dólares
            
            if debug:
                print(f"Dados de uso: {usage_data}")
        
        if subscription_response.status_code == 200:
            subscription_data = subscription_response.json()
            limite_credito = subscription_data.get('hard_limit_usd', 0)
            
            if debug:
                print(f"Dados de subscription: {subscription_data}")
        
        # Se pelo menos uma das consultas funcionou
        if usage_response.status_code == 200 or subscription_response.status_code == 200:
            resultado = {
                'status': 'sucesso',
                'data_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'limite_credito': limite_credito,
                'uso_mensal': uso_mensal,
                'saldo_restante': max(0, limite_credito - uso_mensal),
                'periodo': f'{inicio_mes} a {fim_mes}'
            }
            
            return resultado
        else:
            # Se ambas falharam, tentar método alternativo
            return obter_saldo_alternativo(api_key, debug)
            
    except requests.exceptions.RequestException as e:
        return {
            'status': 'erro',
            'mensagem': f'Erro de conexão: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'erro',
            'mensagem': f'Erro inesperado: {str(e)}'
        }

def obter_saldo_alternativo(api_key, debug=False):
    """
    Método alternativo para obter informações básicas da conta
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Tentar obter informações da organização
        org_url = 'https://api.openai.com/v1/organizations'
        org_response = requests.get(org_url, headers=headers)
        
        if debug:
            print(f"Status organização: {org_response.status_code}")
        
        if org_response.status_code == 200:
            org_data = org_response.json()
            
            return {
                'status': 'info_limitada',
                'data_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mensagem': 'Conectado com sucesso, mas informações de billing podem não estar disponíveis',
                'organizacoes': len(org_data.get('data', [])),
                'api_funcional': True
            }
        else:
            return {
                'status': 'erro',
                'codigo': org_response.status_code,
                'mensagem': 'Não foi possível acessar informações da conta'
            }
            
    except Exception as e:
        return {
            'status': 'erro',
            'mensagem': f'Erro no método alternativo: {str(e)}'
        }

def exibir_saldo(api_key, debug=False):
    """
    Exibe o saldo de forma formatada
    
    Args:
        api_key (str): Sua chave de API da OpenAI
        debug (bool): Se True, exibe informações de debug
    """
    resultado = obter_saldo_openai(api_key, debug)
    
    if resultado['status'] == 'sucesso':
        print("=" * 60)
        print("SALDO DA CONTA OPENAI")
        print("=" * 60)
        print(f"Data da consulta: {resultado['data_consulta']}")
        print(f"Período analisado: {resultado['periodo']}")
        print(f"Limite de crédito: ${resultado['limite_credito']:.2f}")
        print(f"Uso no período: ${resultado['uso_mensal']:.2f}")
        print(f"Saldo restante: ${resultado['saldo_restante']:.2f}")
        print("=" * 60)
        
        # Alertas baseados no saldo
        if resultado['limite_credito'] > 0:
            percentual_usado = (resultado['uso_mensal'] / resultado['limite_credito']) * 100
            if percentual_usado >= 90:
                print("🚨 CRÍTICO: Mais de 90% do limite usado!")
            elif percentual_usado >= 70:
                print("⚠️  ATENÇÃO: Mais de 70% do limite usado")
            elif percentual_usado >= 50:
                print("⚡ Aviso: Mais de 50% do limite usado")
            else:
                print("✅ Uso dentro do limite normal")
                
    elif resultado['status'] == 'info_limitada':
        print("=" * 60)
        print("CONEXÃO COM OPENAI - INFORMAÇÕES LIMITADAS")
        print("=" * 60)
        print(f"Data da consulta: {resultado['data_consulta']}")
        print(f"Status da API: {'✅ Funcional' if resultado['api_funcional'] else '❌ Com problemas'}")
        print(f"Organizações vinculadas: {resultado['organizacoes']}")
        print("=" * 60)
        print("ℹ️  Informações de billing podem não estar disponíveis")
        print("   Isso pode acontecer se a conta não tiver histórico de billing")
        print("   ou se não tiver permissões para acessar esses dados.")
        
    else:
        print("=" * 60)
        print("ERRO AO CONSULTAR SALDO")
        print("=" * 60)
        print(f"Mensagem: {resultado['mensagem']}")
        if 'codigo' in resultado:
            print(f"Código HTTP: {resultado['codigo']}")
        print("=" * 60)
        
        # Sugestões baseadas no tipo de erro
        if 'codigo' in resultado:
            if resultado['codigo'] == 401:
                print("💡 Sugestões:")
                print("   - Verifique se a API key está correta no arquivo .env")
                print("   - Certifique-se de que a API key não expirou")
            elif resultado['codigo'] == 403:
                print("💡 Sugestões:")
                print("   - Sua conta pode não ter permissão para acessar billing")
                print("   - Verifique se a conta tem créditos ou método de pagamento")
            elif resultado['codigo'] == 429:
                print("💡 Sugestões:")
                print("   - Muitas requisições. Aguarde um momento e tente novamente")
        
        print("   - Teste se a API está funcionando em: https://platform.openai.com/playground")

# Exemplo de uso
if __name__ == "__main__":
    # Carregar a chave de API do arquivo .env
    API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Verificar se a chave foi carregada
    if not API_KEY:
        print("❌ Chave de API não encontrada no arquivo .env")
        print("Certifique-se de que o arquivo .env contém:")
        print("OPENAI_API_KEY=sua-chave-api-aqui")
    else:
        print("✅ Chave de API carregada do arquivo .env")
        
        # Para debug detalhado, use:
        # exibir_saldo(API_KEY, debug=True)
        
        exibir_saldo(API_KEY)

# Função simplificada para usar diretamente com .env
def verificar_saldo(debug=False):
    """
    Função simplificada que carrega automaticamente do .env
    
    Args:
        debug (bool): Se True, exibe informações de debug
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Variável OPENAI_API_KEY não encontrada no .env")
        return None
    
    return exibir_saldo(api_key, debug)

# Função apenas para testar conectividade
def testar_api():
    """
    Testa apenas se a API key está funcionando
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ API key não encontrada no .env")
        return False
        
    headers = {'Authorization': f'Bearer {api_key}'}
    
    try:
        response = requests.get('https://api.openai.com/v1/models', headers=headers)
        if response.status_code == 200:
            print("✅ API key está funcionando!")
            models = response.json()
            print(f"📋 {len(models.get('data', []))} modelos disponíveis")
            return True
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False