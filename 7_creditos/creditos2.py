import openai
import os
from datetime import datetime, timedelta

def get_openai_balance():
    try:
        client = openai.OpenAI()

        # O endpoint correto para obter informações de crédito/faturamento é geralmente
        # client.billing.list_credit_grants() ou client.beta.billing.list_credit_grants()
        # Dependendo da versão exata da API e se é um endpoint beta.
        # Vamos tentar a forma mais comum: list_credit_grants().
        # Este método retorna um objeto CreditGrant (ou uma lista deles, se houver múltiplos).

        # Tente acessar credit_grants diretamente:
        credit_grants = client.billing.list_credit_grants()

        # O objeto credit_grants.data é uma lista de concessões.
        # Cada concessão pode ter 'amount_granted', 'amount_used', 'expires_at'.
        # Precisamos somar isso para ter o total.

        total_granted = 0.0
        total_used = 0.0
        total_available = 0.0
        latest_access_until = datetime(1970, 1, 1) # Data inicial muito antiga

        for grant in credit_grants.data:
            # Verifica se 'amount_granted' e 'amount_used' existem no objeto grant
            # e são numéricos antes de somar.
            if hasattr(grant, 'amount_granted') and isinstance(grant.amount_granted, (int, float)):
                total_granted += grant.amount_granted
            if hasattr(grant, 'amount_used') and isinstance(grant.amount_used, (int, float)):
                total_used += grant.amount_used

            if hasattr(grant, 'expires_at') and grant.expires_at is not None:
                expires_at_dt = datetime.fromtimestamp(grant.expires_at)
                if expires_at_dt > latest_access_until:
                    latest_access_until = expires_at_dt

        total_available = total_granted - total_used

        print(f"Informações de Faturamento da OpenAI:")
        print(f"Total de Crédito Concedido: ${total_granted:.2f}")
        print(f"Total Gasto até o momento: ${total_used:.2f}")
        print(f"Total Disponível: ${total_available:.2f}")
        print(f"Créditos Válidos Até: {latest_access_until.strftime('%Y-%m-%d %H:%M:%S')}")

        return {
            "total_granted": total_granted,
            "total_spent": total_used, # Renomeado para consistência com o que a API geralmente retorna
            "total_available": total_available,
            "access_until": latest_access_until.strftime('%Y-%m-%d %H:%M:%S')
        }

    except openai.AuthenticationError:
        print("Erro de Autenticação: Sua chave de API está inválida ou ausente. Verifique a variável de ambiente OPENAI_API_KEY.")
        return None
    except openai.APIStatusError as e:
        print(f"Erro na API da OpenAI (Status: {e.status_code}): {e.response.json() if hasattr(e.response, 'json') else e.response}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return None

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("ATENÇÃO: A variável de ambiente OPENAI_API_KEY não está definida.")
        print("Por favor, defina-a antes de executar este script para autenticação com a API da OpenAI.")
        print("Ex: export OPENAI_API_KEY='sk-sua_chave_aqui' (Linux/macOS)")
        print("Ex: $env:OPENAI_API_KEY='sk-sua_chave_aqui' (Windows PowerShell)")
    else:
        balance_info = get_openai_balance()
        if balance_info:
            print("\nVerificação de saldo concluída.")
            print(f"Total de Crédito Concedido: ${balance_info['total_granted']:.2f}")
            print(f"Total Gasto até o momento: ${balance_info['total_spent']:.2f}")
            print(f"Total Disponível: ${balance_info['total_available']:.2f}")
            print(f"Créditos Válidos Até: {balance_info['access_until']}")