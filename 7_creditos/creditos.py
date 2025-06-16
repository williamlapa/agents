import requests
import json
from datetime import datetime
from typing import Dict, Optional
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class CreditInfo:
    platform: str
    balance: Optional[float] = None
    currency: str = "USD"
    limit: Optional[float] = None
    usage: Optional[float] = None
    error: Optional[str] = None

class APICreditsMonitor:
    def __init__(self):
        self.platforms = {
            'openai': self.get_openai_credits,
            'anthropic': self.get_anthropic_credits,
            'google': self.get_google_credits,
            'deepseek': self.get_deepseek_credits
        }
        
    def get_openai_credits(self, api_key: str) -> CreditInfo:
        """Obtém créditos da OpenAI"""
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Primeiro, testa se a API está funcionando
            test_url = 'https://api.openai.com/v1/models'
            test_response = requests.get(test_url, headers=headers)
            
            if test_response.status_code != 200:
                return CreditInfo(
                    platform="OpenAI",
                    error=f"Chave API inválida ou erro de autenticação: {test_response.status_code}"
                )
            
            # Tenta obter informações de billing (pode não funcionar para todos os tipos de conta)
            billing_url = 'https://api.openai.com/v1/dashboard/billing/credit_grants'
            billing_response = requests.get(billing_url, headers=headers)
            
            if billing_response.status_code == 200:
                billing_data = billing_response.json()
                total_granted = sum(grant.get('grant_amount', 0) for grant in billing_data.get('data', []))
                total_used = sum(grant.get('used_amount', 0) for grant in billing_data.get('data', []))
                balance = total_granted - total_used
                
                return CreditInfo(
                    platform="OpenAI",
                    balance=balance,
                    usage=total_used,
                    limit=total_granted,
                    currency="USD"
                )
            else:
                # Se não conseguir acessar billing, pelo menos confirma que a API funciona
                return CreditInfo(
                    platform="OpenAI",
                    error="API ativa - Acesso ao billing negado (verifique tipo de conta)"
                )
                    
        except Exception as e:
            return CreditInfo(platform="OpenAI", error=str(e))
    
    def get_anthropic_credits(self, api_key: str) -> CreditInfo:
        """Obtém créditos da Anthropic (Claude)"""
        try:
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # Testa a API com uma requisição mínima
            url = 'https://api.anthropic.com/v1/messages'
            test_data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Test"}]
            }
            
            response = requests.post(url, headers=headers, json=test_data)
            
            if response.status_code == 200:
                return CreditInfo(
                    platform="Anthropic (Claude)",
                    error="API ativa - Consulte saldo no console Anthropic"
                )
            elif response.status_code == 401:
                return CreditInfo(
                    platform="Anthropic (Claude)",
                    error="Chave API inválida ou expirada"
                )
            elif response.status_code == 429:
                return CreditInfo(
                    platform="Anthropic (Claude)",
                    error="Limite de requisições atingido - API funcional"
                )
            else:
                return CreditInfo(
                    platform="Anthropic (Claude)",
                    error=f"Erro na API: {response.status_code}"
                )
                
        except Exception as e:
            return CreditInfo(platform="Anthropic (Claude)", error=str(e))
    
    def get_google_credits(self, api_key: str) -> CreditInfo:
        """Obtém créditos do Google AI (Gemini)"""
        try:
            # Google AI Studio não tem endpoint direto para billing
            # Vamos verificar se a chave funciona
            url = f'https://generativelanguage.googleapis.com/v1/models?key={api_key}'
            
            response = requests.get(url)
            
            if response.status_code == 200:
                return CreditInfo(
                    platform="Google AI (Gemini)",
                    error="API ativa - Consulte saldo no Google Cloud Console"
                )
            else:
                return CreditInfo(
                    platform="Google AI (Gemini)",
                    error=f"Erro na API: {response.status_code}"
                )
                
        except Exception as e:
            return CreditInfo(platform="Google AI (Gemini)", error=str(e))
    
    def get_deepseek_credits(self, api_key: str) -> CreditInfo:
        """Obtém créditos da DeepSeek"""
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # DeepSeek usa endpoint similar ao OpenAI
            url = 'https://api.deepseek.com/v1/user/balance'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return CreditInfo(
                    platform="DeepSeek",
                    balance=data.get('balance', 0),
                    currency="USD"
                )
            else:
                # Tenta verificar se a API está ativa
                test_url = 'https://api.deepseek.com/v1/models'
                test_response = requests.get(test_url, headers=headers)
                
                if test_response.status_code == 200:
                    return CreditInfo(
                        platform="DeepSeek",
                        error="API ativa - Endpoint de saldo indisponível"
                    )
                else:
                    return CreditInfo(
                        platform="DeepSeek",
                        error=f"Erro na API: {response.status_code}"
                    )
                    
        except Exception as e:
            return CreditInfo(platform="DeepSeek", error=str(e))
    
    def check_all_credits(self, api_keys: Dict[str, str]) -> Dict[str, CreditInfo]:
        """Verifica créditos de todas as plataformas"""
        results = {}
        
        for platform, api_key in api_keys.items():
            if not api_key:
                results[platform] = CreditInfo(
                    platform=platform,
                    error="Chave API não encontrada no arquivo .env"
                )
                continue
                
            if platform in self.platforms:
                print(f"Verificando {platform}...")
                results[platform] = self.platforms[platform](api_key)
            else:
                results[platform] = CreditInfo(
                    platform=platform,
                    error="Plataforma não suportada"
                )
        
        return results
    
    def print_report(self, results: Dict[str, CreditInfo]):
        """Imprime relatório formatado"""
        print("\n" + "="*60)
        print(f"RELATÓRIO DE CRÉDITOS - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        
        for platform, info in results.items():
            print(f"\n🔹 {info.platform}")
            print("-" * 30)
            
            if info.error:
                print(f"❌ Status: {info.error}")
            else:
                if info.balance is not None:
                    print(f"💰 Saldo: {info.balance:.2f} {info.currency}")
                if info.limit is not None:
                    print(f"📊 Limite: {info.limit:.2f} {info.currency}")
                if info.usage is not None:
                    print(f"📈 Uso: {info.usage:.2f} {info.currency}")
                if not any([info.balance, info.limit, info.usage]):
                    print("✅ API ativa - Consulte saldo no console da plataforma")
        
        print("\n" + "="*60)

def main():
    """Função principal"""
    # Verifica se o arquivo .env existe
    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado!")
        print("\n📝 Crie um arquivo .env na mesma pasta do script com o seguinte formato:")
        print("OPENAI_API_KEY=sua_chave_openai")
        print("ANTHROPIC_API_KEY=sua_chave_anthropic")
        print("GOOGLE_API_KEY=sua_chave_google")
        print("DEEPSEEK_API_KEY=sua_chave_deepseek")
        return
    
    # Carrega variáveis do arquivo .env
    load_dotenv()
    
    monitor = APICreditsMonitor()
    
    # Carrega as chaves API do arquivo .env
    api_keys = {
        'openai': os.getenv('OPENAI_API_KEY'),
        'anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'google': os.getenv('GOOGLE_API_KEY'),
        'deepseek': os.getenv('DEEPSEEK_API_KEY')
    }
    
    # Verifica se alguma chave está faltando
    missing_keys = [platform for platform, key in api_keys.items() if not key]
    if missing_keys:
        print(f"⚠️  Chaves API não encontradas no .env: {', '.join(missing_keys)}")
        print("Continuando com as chaves disponíveis...\n")
    
    print("Iniciando verificação de créditos...")
    results = monitor.check_all_credits(api_keys)
    monitor.print_report(results)
    
    # Salva resultados em JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'credits_report_{timestamp}.json'
    
    # Converte para dict serializável
    json_results = {}
    for platform, info in results.items():
        json_results[platform] = {
            'platform': info.platform,
            'balance': info.balance,
            'currency': info.currency,
            'limit': info.limit,
            'usage': info.usage,
            'error': info.error,
            'timestamp': datetime.now().isoformat()
        }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório salvo em: {filename}")

if __name__ == "__main__":
    main()