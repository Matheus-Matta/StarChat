import requests
import logging
from typing import Any, Dict, List, Optional
from django.conf import settings
from .exceptions import ChatwootAPIError, ChatwootConfigurationError

logger = logging.getLogger(__name__)


class ChatwootClient:
    """Cliente para interação com a API do Chatwoot Platform."""
    
    DEFAULT_TIMEOUT = 30
    DEFAULT_LOCALE = "pt_BR"
    DEFAULT_STATUS = "active"
    
    def __init__(self):
        self._validate_configuration()
        self.base_url = self._normalize_base_url(settings.CHATWOOT_URL)
        self.headers = self._build_headers(settings.CHATWOOT_API_TOKEN)
    
    def _validate_configuration(self) -> None:
        """Valida se as configurações necessárias estão presentes."""
        required_settings = ['CHATWOOT_URL', 'CHATWOOT_API_TOKEN']
        missing_settings = [
            setting for setting in required_settings 
            if not hasattr(settings, setting) or not getattr(settings, setting)
        ]
        
        if missing_settings:
            raise ChatwootConfigurationError(
                f"Configurações obrigatórias não encontradas: {', '.join(missing_settings)}"
            )
    
    def _normalize_base_url(self, url: str) -> str:
        """Normaliza a URL base removendo barras no final."""
        if not url:
            raise ChatwootConfigurationError("CHATWOOT_URL não pode estar vazio")
        return url.rstrip("/")
    
    def _build_headers(self, access_token: str = None) -> Dict[str, str]:
        """Constrói os headers padrão para as requisições."""
        return {
            "api_access_token": access_token,
            "Content-Type": "application/json",
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        access_token: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executa uma requisição HTTP e trata erros de forma consistente.
        
        Args:
            method: Método HTTP (GET, POST, PATCH, DELETE)
            endpoint: Endpoint da API (sem a base URL)
            payload: Dados para enviar na requisição
            timeout: Timeout em segundos
            
        Returns:
            Resposta JSON ou None em caso de erro
            
        Raises:
            ChatwootAPIError: Em caso de erro na API
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"Enviando {method.upper()} para {url}")
        if payload:
            logger.debug(f"Payload: {payload}")
        
        try:
            headers = self._build_headers(access_token) if access_token else self.headers
            print("HEADERS",headers)
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            if response.raise_for_status():
                return False
            
            logger.debug(f"Recebido status_code {response.status_code}")
            
            # DELETE requests podem não retornar JSON
            if method.upper() == 'DELETE':
                return {"success": response.status_code == 200}
            
            return response.json()
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout ao fazer {method.upper()} para {url}"
            logger.error(error_msg)
            return False
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro HTTP ao fazer {method.upper()} para {url}: {e}"
            logger.error(error_msg)
            if hasattr(e.response, 'text'):
                logger.error(f"Resposta do servidor: {e.response.text}")
            return False
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de rede ao fazer {method.upper()} para {url}: {e}"
            logger.error(error_msg)
            return False
    
    def create_account(
        self, 
        name: str, 
        website_url: Optional[str] = None, 
        features: Optional[Dict[str, Any]] = None,
        locale: str = DEFAULT_LOCALE,
        status: str = DEFAULT_STATUS
    ) -> Optional[int]:
        """
        Cria uma nova conta no Chatwoot.
        
        Args:
            name: Nome da conta
            website_url: URL do website (opcional)
            features: Features a serem habilitadas (opcional)
            locale: Localização (padrão: pt_BR)
            status: Status da conta (padrão: active)
            
        Returns:
            ID da conta criada ou None em caso de erro
        """
        if not name or not name.strip():
            raise ValueError("Nome da conta é obrigatório")
        
        payload = {
            "name": name.strip(),
            "locale": locale,
            "status": status,
            "limits": {"agents": 1, "inboxes": 1},
        }
        
        if website_url:
            payload["domain"] = website_url.strip()
            
        if features is not None:
            payload["features"] = features
        
        endpoint = "/platform/api/v1/accounts"
        response = self._make_request("POST", endpoint, payload)
        
        return response.get("id") if response else None
    
    def update_account(
        self, 
        account_id: int, 
        name: Optional[str] = None, 
        website_url: Optional[str] = None,
        limits: Optional[Dict[str, int]] = None, 
        features: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma conta existente no Chatwoot.
        
        Args:
            account_id: ID da conta a ser atualizada
            name: Novo nome da conta (opcional)
            website_url: Nova URL do website (opcional)
            limits: Novos limites (opcional)
            features: Novas features (opcional)
            
        Returns:
            Dados da conta atualizada ou None em caso de erro
        """
        if not account_id or account_id <= 0:
            raise ValueError("ID da conta deve ser um número positivo")
        
        payload = {}
        
        if name:
            payload["name"] = name.strip()
        if website_url:
            payload["domain"] = website_url.strip()
        if limits:
            payload["limits"] = limits
        if features is not None:
            logger.debug(f"Atualizando features: {features}")
            payload["features"] = features
        
        if not payload:
            return None
        
        endpoint = f"/platform/api/v1/accounts/{account_id}"
        return self._make_request("PATCH", endpoint, payload)
    
    def delete_account(self, account_id: int) -> bool:
        """
        Deleta uma conta no Chatwoot.
        
        Args:
            account_id: ID da conta a ser deletada
            
        Returns:
            True se a conta foi deletada com sucesso, False caso contrário
        """
        if not account_id or account_id <= 0:
            raise ValueError("ID da conta deve ser um número positivo")
        
        endpoint = f"/platform/api/v1/accounts/{account_id}"
        response = self._make_request("DELETE", endpoint)
        
        return response.get("success", False) if response else False
    
    def create_user(
        self, 
        account_id: int,
        name: str, 
        email: str, 
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um usuário dentro de uma conta Chatwoot.
        
        Args:
            account_id: ID da conta onde o usuário será criado
            name: Nome do usuário
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            Dados do usuário criado (incluindo ID) ou None em caso de erro
        """
        if not account_id or account_id <= 0:
            raise ValueError("ID da conta deve ser um número positivo")
        
        if not all([name, email, password]):
            raise ValueError("Nome, email e senha são obrigatórios")
        
        if not self._is_valid_email(email):
            raise ValueError("Email inválido")
        
        payload = {
            "name": name.strip(),
            "display_name": name.strip(),
            "email": email.strip().lower(),
            "password": password,
        }
        
        endpoint = f"/platform/api/v1/users"
        return self._make_request("POST", endpoint, payload)
    
    def create_account_user(
        self, 
        account_id: int, 
        user_id: int, 
        role: str = "agent"
    ) -> Optional[Dict[str, Any]]:
        """
        Adiciona um usuário existente a uma conta Chatwoot.
        
        Args:
            account_id: ID da conta
            user_id: ID do usuário
            role: Role do usuário (padrão: agent)
            
        Returns:
            Dados da associação criada ou None em caso de erro
        """
        if not account_id or account_id <= 0:
            raise ValueError("ID da conta deve ser um número positivo")
        
        if not user_id or user_id <= 0:
            raise ValueError("ID do usuário deve ser um número positivo")
        
        valid_roles = ["agent", "administrator"]
        if role not in valid_roles:
            raise ValueError(f"Role deve ser um dos seguintes: {', '.join(valid_roles)}")
        
        payload = {
            "user_id": user_id,
            "role": role
        }
        
        endpoint = f"/platform/api/v1/accounts/{account_id}/account_users"
        return self._make_request("POST", endpoint, payload)
    
    def update_user(
        self,
        user_id: int,
        name: Optional[str]   = None,
        email: Optional[str]  = None,
        password: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza os dados de um usuário Chatwoot.
        PATCH /platform/api/v1/users/{user_id}
        """
        if user_id <= 0:
            raise ValueError("ID deve ser um número positivo")

        payload: Dict[str, Any] = {}
        if name:
            payload["name"] = name.strip()
            payload["display_name"] = name.strip()
        if email:
            payload["email"] = email.strip().lower()
        if password:
            payload["password"] = password
        if not payload:
            return None

        endpoint = f"/platform/api/v1/users/{user_id}"
        return self._make_request("PATCH", endpoint, payload)

    def delete_user(
        self,
        user_id: int
    ) -> bool:
        """
        Exclui um usuário de uma conta Chatwoot.
        DELETE /platform/api/v1/users/{user_id}
        """
        if not user_id:
            return False

        endpoint = f"/platform/api/v1/users/{user_id}"
        response = self._make_request("DELETE", endpoint)
        return bool(response and response.get("success", False))
    
    def get_user(
        self,
        user_id: int
    ) -> bool:
        """
        Recupera um usuário de uma conta Chatwoot.
        GET /platform/api/v1/users/{user_id}
        """
        if not user_id:
            return False

        endpoint = f"/platform/api/v1/users/{user_id}"
        response = self._make_request("GET", endpoint)
        return response
         
    def _is_valid_email(self, email: str) -> bool:
        """Validação básica de email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_agent(
        self,
        account_id: int,
        name: str,
        email: str,
        role: str = "agent",
        password: Optional[str] = None,
        confirmed_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adiciona um novo agente a uma conta Chatwoot, podendo passar senha e confirmed_at.
        POST /platform/api/v1/accounts/{account_id}/agents
        """
        payload = {
            "name":                name.strip(),
            "email":               email.strip().lower(),
            "role":                role,
            "availability_status": "available",
            "auto_offline":        1,
        }

        if password:
            payload["password"] = password
        if confirmed_at:
            payload["confirmed_at"] = confirmed_at
        endpoint = f"/api/v1/accounts/{account_id}/agents"
        return self._make_request("POST", endpoint, payload)

    def list_agents(self, account_id: int, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os agentes de uma conta.
        GET /platform/api/v1/accounts/{account_id}/agents
        """
        if account_id <= 0:
            raise ValueError("ID da conta deve ser positivo")

        endpoint = f"/api/v1/accounts/{account_id}/agents"
        resp = self._make_request("GET", endpoint, access_token=access_token)
        return resp or []

    def update_agent(
        self,
        account_id: int,
        agent_id: int,
        role: str,
    ) -> Dict[str, Any]:
        """
        Atualiza um agente (role ou status).
        PATCH /platform/api/v1/accounts/{account_id}/agents/{agent_id}
        """
        payload: Dict[str, Any] = {}
        if role:
            payload["role"] = role
        endpoint = f"/platform/api/v1/accounts/{account_id}/agents/{agent_id}"
        return self._make_request("PATCH", endpoint, payload)

    def delete_agent(
        self,
        account_id: int,
        agent_id: int
    ) -> bool:
        """
        Remove um agente da conta.
        DELETE /platform/api/v1/accounts/{account_id}/agents/{agent_id}
        """
        if not account_id or not agent_id:
            return False

        endpoint = f"/platform/api/v1/accounts/{account_id}/agents/{agent_id}"
        resp = self._make_request("DELETE", endpoint)
        return bool(resp and resp.get("success", False))
    
    def list_inboxes(
        self,
        account_id: int,
        access_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        GET  /api/v1/accounts/{account_id}/inboxes
        Returns all inboxes for the given account.
        """
        endpoint = f"/api/v1/accounts/{account_id}/inboxes"
        resp = self._make_request("GET", endpoint, access_token=access_token)
        # Chatwoot typically wraps lists under "payload" or returns raw list:
        if isinstance(resp, dict) and resp.get("payload") is not None:
            return resp["payload"]
        return resp or []

    def create_inbox(
        self,
        account_id: int,
        name: str,
        channel_type: str,
        provider_config: Dict[str, Any],
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        POST /api/v1/accounts/{account_id}/inboxes
        Creates a new inbox under the account.
        """
        payload = {
            "name": name.strip(),
            "channel": channel_type,
            "provider_config": provider_config,
        }
        endpoint = f"/api/v1/accounts/{account_id}/inboxes"
        return self._make_request("POST", endpoint, payload, access_token=access_token)

    def update_inbox(
        self,
        account_id: int,
        inbox_id: int,
        name: Optional[str] = None,
        provider_config: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        PATCH /api/v1/accounts/{account_id}/inboxes/{inbox_id}
        Updates an existing inbox (name, config, etc.).
        """
        payload: Dict[str, Any] = {}
        if name:
            payload["name"] = name.strip()
        if provider_config is not None:
            payload["provider_config"] = provider_config

        if not payload:
            return None

        endpoint = f"/api/v1/accounts/{account_id}/inboxes/{inbox_id}"
        return self._make_request("PATCH", endpoint, payload, access_token=access_token)

    def delete_inbox(
        self,
        account_id: int,
        inbox_id: int,
        access_token: Optional[str] = None
    ) -> bool:
        """
        DELETE /api/v1/accounts/{account_id}/inboxes/{inbox_id}
        Removes an inbox.
        """
        endpoint = f"/api/v1/accounts/{account_id}/inboxes/{inbox_id}"
        resp = self._make_request("DELETE", endpoint, access_token=access_token)
        return bool(resp and resp.get("success", False))