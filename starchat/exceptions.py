# exceptions.py
"""
Exceções customizadas para o cliente Chatwoot.

Este módulo define uma hierarquia de exceções específicas para tratar
diferentes tipos de erros que podem ocorrer ao interagir com a API do Chatwoot.
"""

from typing import Optional, Dict, Any


class ChatwootError(Exception):
    """
    Exceção base para todos os erros relacionados ao Chatwoot.
    
    Attributes:
        message: Mensagem de erro
        details: Detalhes adicionais sobre o erro
        status_code: Código de status HTTP (se aplicável)
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self) -> str:
        base_msg = self.message
        if self.status_code:
            base_msg = f"[{self.status_code}] {base_msg}"
        if self.details:
            base_msg = f"{base_msg} - Detalhes: {self.details}"
        return base_msg


class ChatwootConfigurationError(ChatwootError):
    """
    Erro de configuração do Chatwoot.
    
    Levantado quando configurações obrigatórias estão ausentes ou inválidas.
    """
    
    def __init__(self, message: str, missing_configs: Optional[list] = None):
        self.missing_configs = missing_configs or []
        details = {"missing_configs": self.missing_configs} if self.missing_configs else None
        super().__init__(message, details)


class ChatwootAPIError(ChatwootError):
    """
    Erro na comunicação com a API do Chatwoot.
    
    Levantado quando ocorrem erros HTTP ou de rede ao fazer requisições.
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        self.response_body = response_body
        self.endpoint = endpoint
        details = {}
        
        if response_body:
            details["response_body"] = response_body
        if endpoint:
            details["endpoint"] = endpoint
            
        super().__init__(message, details, status_code)


class ChatwootValidationError(ChatwootError):
    """
    Erro de validação de dados do Chatwoot.
    
    Levantado quando os dados fornecidos não atendem aos critérios de validação.
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.field = field
        self.value = value
        details = {}
        
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)
            
        super().__init__(message, details)


class ChatwootAuthenticationError(ChatwootAPIError):
    """
    Erro de autenticação com a API do Chatwoot.
    
    Levantado quando o token de API é inválido ou expirado.
    """
    
    def __init__(self, message: str = "Token de API inválido ou expirado"):
        super().__init__(message, status_code=401)


class ChatwootAuthorizationError(ChatwootAPIError):
    """
    Erro de autorização com a API do Chatwoot.
    
    Levantado quando o usuário não tem permissão para realizar a operação.
    """
    
    def __init__(self, message: str = "Permissão insuficiente para realizar esta operação"):
        super().__init__(message, status_code=403)


class ChatwootNotFoundError(ChatwootAPIError):
    """
    Erro quando um recurso não é encontrado no Chatwoot.
    
    Levantado quando se tenta acessar um recurso que não existe.
    """
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[Any] = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        details = {}
        
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id is not None:
            details["resource_id"] = str(resource_id)
            
        super().__init__(message, status_code=404, details=details)


class ChatwootRateLimitError(ChatwootAPIError):
    """
    Erro de limite de taxa da API do Chatwoot.
    
    Levantado quando o limite de requisições por período é excedido.
    """
    
    def __init__(
        self, 
        message: str = "Limite de requisições excedido",
        retry_after: Optional[int] = None
    ):
        self.retry_after = retry_after
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(message, status_code=429, details=details)


class ChatwootTimeoutError(ChatwootError):
    """
    Erro de timeout na comunicação com o Chatwoot.
    
    Levantado quando uma requisição excede o tempo limite.
    """
    
    def __init__(self, message: str = "Timeout na requisição", timeout: Optional[int] = None):
        self.timeout = timeout
        details = {"timeout": timeout} if timeout else None
        super().__init__(message, details)


class ChatwootServerError(ChatwootAPIError):
    """
    Erro interno do servidor Chatwoot.
    
    Levantado para erros 5xx do servidor.
    """
    
    def __init__(self, message: str = "Erro interno do servidor Chatwoot", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class ChatwootAccountError(ChatwootError):
    """
    Erro específico relacionado a contas do Chatwoot.
    
    Levantado para operações inválidas em contas.
    """
    
    def __init__(self, message: str, account_id: Optional[int] = None):
        self.account_id = account_id
        details = {"account_id": account_id} if account_id else None
        super().__init__(message, details)


class ChatwootUserError(ChatwootError):
    """
    Erro específico relacionado a usuários do Chatwoot.
    
    Levantado para operações inválidas em usuários.
    """
    
    def __init__(self, message: str, user_id: Optional[int] = None, email: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        details = {}
        
        if user_id:
            details["user_id"] = user_id
        if email:
            details["email"] = email
            
        super().__init__(message, details)


class ChatwootNetworkError(ChatwootError):
    """
    Erro de rede na comunicação com o Chatwoot.
    
    Levantado para problemas de conectividade.
    """
    
    def __init__(self, message: str = "Erro de conectividade com o Chatwoot"):
        super().__init__(message)


# Factory function para criar exceções baseadas no status code
def create_api_error_from_response(
    status_code: int,
    message: str,
    response_body: Optional[str] = None,
    endpoint: Optional[str] = None
) -> ChatwootAPIError:
    """
    Cria a exceção apropriada baseada no código de status HTTP.
    
    Args:
        status_code: Código de status HTTP
        message: Mensagem de erro
        response_body: Corpo da resposta (opcional)
        endpoint: Endpoint da requisição (opcional)
        
    Returns:
        Instância da exceção apropriada
    """
    error_mapping = {
        401: ChatwootAuthenticationError,
        403: ChatwootAuthorizationError,
        404: ChatwootNotFoundError,
        429: ChatwootRateLimitError,
        500: ChatwootServerError,
        502: ChatwootServerError,
        503: ChatwootServerError,
        504: ChatwootServerError,
    }
    
    error_class = error_mapping.get(status_code, ChatwootAPIError)
    
    if error_class in [ChatwootAuthenticationError, ChatwootAuthorizationError, ChatwootRateLimitError]:
        return error_class(message)
    elif error_class == ChatwootServerError:
        return error_class(message, status_code)
    else:
        return error_class(message, status_code, response_body, endpoint)