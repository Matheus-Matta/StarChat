import logging
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps
from django.apps import apps
from .client import ChatwootClient
from .features import CHATWOOT_FEATURES
from .decorator import handle_chatwoot_exceptions
from .exceptions import ChatwootNotFoundError
from accounts.models import Account
from django.utils import timezone
logger = logging.getLogger(__name__)
    
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import get_user_model
User = get_user_model()

class ChatwootAccountService:
    """Service class to handle Chatwoot account operations."""
    
    def __init__(self):
        self.client = ChatwootClient()
        self.ChatwootAccount = apps.get_model("starchat", "ChatwootAccount")
        
    def _get_account_limits(self, account: Account) -> Dict[str, int]:
        """
        Returns the account limits configuration.
        
        Args:
            account: The Account instance.
            
        Returns:
            Dictionary with agents and inboxes limits.
        """
        agents = account.extra_agents + account.plan.included_agents
        inboxes = account.extra_inboxes + account.plan.included_inboxes
        
        return {
            "agents": agents if agents > 0 else 1,
            "inboxes": inboxes if inboxes > 0 else 1,
        }
    
    @staticmethod
    def _is_valid_account_id(account_id: Any) -> bool:
        """
        Validates if the account ID is valid.
        
        Args:
            account_id: The account ID to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        return isinstance(account_id, int) and account_id > 0
       
    def get_enabled_features(self) -> Dict[str, bool]:
        """
        Returns a dictionary with only enabled features.
        
        Returns:
            Dict with feature names as keys and True as values for enabled features.
        """
        features = CHATWOOT_FEATURES.get("features", {})
        return {name: enabled for name, enabled in features.items() if enabled}
    
    def create_chatwoot_account(self, account: Account) -> None:
        """
        Creates a new Chatwoot account with associated user and permissions.
        
        Args:
            account: The Account instance to create Chatwoot account for.
            
        Raises:
            ValueError: If account creation fails or returns invalid data.
            Exception: For any other errors during account creation.
        """
        try:
            chatwoot_id = self._create_account(account)
            
            logger.info(f"Successfully created Chatwoot account {chatwoot_id} for {account}")
            return chatwoot_id
        except Exception as e:
            logger.error(f"Error creating Chatwoot account for {account}: {e}")
            return False
    
    def _create_account(self, account: Account) -> int:
        """Creates the Chatwoot account and validates the response."""
        try:
            chatwoot_id = self.client.create_account(
                name=str(account.email),
                status=account.status,
                website_url=getattr(account, "website_url", None),
                features=self.get_enabled_features()
            )
            if not chatwoot_id:
                error_msg = f"Failed to create Chatwoot account for {account}"
                logger.error(error_msg)
                return False
            
            if not self._is_valid_account_id(chatwoot_id):
                error_msg = f"Invalid Chatwoot account id: {chatwoot_id}"
                logger.error(f"Error creating Chatwoot account for {account}: {error_msg}")
                return False
            
            self.ChatwootAccount.objects.create(account=account, chatwoot_id=chatwoot_id)
            logger.debug(f"Created Chatwoot account {chatwoot_id} for {account}")
            return chatwoot_id
        except Exception as e:
            logger.error(f"Error creating Chatwoot account: {e}")
            return False
    
    

    def update_chatwoot_account(self, account: Account) -> None:
        """
        Updates an existing Chatwoot account.
        """
        try:
            # tenta obter a instância relacionada
            chatwoot_account = account.chatwoot_account
        except ObjectDoesNotExist:
            logger.warning(f"Não foi possível encontrar ChatwootAccount para {account}")
            return False

        try:
            logger.debug(
                f"Updating Chatwoot account {chatwoot_account.chatwoot_id} for {account}"
            )
            self.client.update_account(
                account_id=chatwoot_account.chatwoot_id,
                name=str(account.email),
                status=account.status,
                website_url=getattr(account, "website_url", None),
                limits=self._get_account_limits(account),
                features=self.get_enabled_features(),
            )
            logger.info(
                f"Successfully updated Chatwoot account {chatwoot_account.chatwoot_id} for {account}"
            )
        except Exception as e:
            logger.error(f"Error updating Chatwoot account: {e}")
            return
        
    def delete_chatwoot_account(self, account: Account) -> None:
        """
        Deletes a Chatwoot account.
        
        Args:
            account: The Account instance whose Chatwoot account should be deleted.
        """
        try:
            chatwoot_account = account.chatwoot_account
            logger.debug(f"Deleting Chatwoot account {chatwoot_account.chatwoot_id} for {account}")
            
            self.client.delete_account(account_id=chatwoot_account.chatwoot_id)
            
            logger.info(f"Successfully deleted Chatwoot account {chatwoot_account.chatwoot_id} for {account}")
            
        except Exception as e:
            logger.error(f"Error deleting Chatwoot account for: {e}")
            return False
    
    @handle_chatwoot_exceptions("create_chatwoot_user")
    def _create_chatwoot_user(self, user: User) -> Dict[str, Any]:
        """Creates a user in Chatwoot and validates the response."""
        try:
            raw_pwd = getattr(user, "_raw_password", None)
            if not raw_pwd:
                logger.error(f"User {user} does not have a raw password set.")
                return False
            
            if not user.account.chatwoot_account:
                logger.error(f"Account {user.account} does not have a Chatwoot set.")
                return False
            
            chatwoot_id = user.account.chatwoot_account.chatwoot_id
            if not chatwoot_id:
                logger.error(f"Chatwoot account {user.account.chatwoot_account} does not have an id set.")
                return False
                
            user_data = self.client.create_user(
                account_id=chatwoot_id,
                name=user.first_name or user.email,
                email=user.email,
                password=raw_pwd
            )
            
            user.user_chatwoot_id = user_data.get('id')
            user.save()
            logger.debug(f"Created user {raw_pwd , user.password} for Chatwoot account {chatwoot_id}")
            
            if not user_data or 'id' not in user_data:
                error_msg = f"Failed to create user in Chatwoot for account {chatwoot_id}"
                logger.error(error_msg)
                return False
            
            logger.debug(f"Created user {user_data['id']} for Chatwoot account {chatwoot_id}")
            
            self._create_account_user_association(chatwoot_id, user.user_chatwoot_id, user.role)
            return user_data
        
        except Exception as e:
            logger.error(f"Error creating user in Chatwoot for account {e}")
            return False
    
    @handle_chatwoot_exceptions("create_account_user_association")
    def _create_account_user_association(self, chatwoot_id: int, user_id: int, role: str = "agent") -> None:
        """Creates the account-user association in Chatwoot."""
        account_user = self.client.create_account_user(
            account_id=chatwoot_id,
            user_id=user_id,
            role=role,
        )
        
        if not account_user:
            error_msg = f"Failed to create account user association for Chatwoot account {chatwoot_id}"
            logger.error(error_msg)
            return False
        logger.debug(f"Created account user association for Chatwoot account {chatwoot_id}")
        
    @handle_chatwoot_exceptions("update_chatwoot_user")
    def _get_chatwoot_user(self, user_id: int) -> Dict[str, Any]:
        """Obtém os detalhes de um usuário existente no Chatwoot."""
        try:
            resp = self.client.get_user(
                user_id=user_id,
            )
            if not resp:
                logger.warning(f"Nenhum dado encontrado para Chatwoot user {user_id}.")

            return resp
        except Exception as e:
            logger.warning(f"Erro ao atualizar Chatwoot user: {e}")
                    
    @handle_chatwoot_exceptions("update_chatwoot_user")
    def _update_chatwoot_user(self, user: User) -> None:
        """Atualiza nome/email/senha de um usuário já existente no Chatwoot."""
        try:
            resp = self.client.update_user(
                user_id=user.user_chatwoot_id,
                name=user.get_full_name() or user.email,
                email=user.email,
            )
            self._create_account_user_association(
                chatwoot_id=user.account.chatwoot_account.chatwoot_id,
                user_id=user.user_chatwoot_id,
                role=user.role
            )
            if resp:
                logger.info(f"Usuário Chatwoot {user.user_chatwoot_id} atualizado.")
            else:
                logger.warning(f"Nada atualizou para Chatwoot user {user.user_chatwoot_id}.")

        except Exception as e:
            logger.warning(f"Erro ao atualizar Chatwoot user: {e}")


    @handle_chatwoot_exceptions("delete_chatwoot_user", allow_not_found=True)
    def _delete_user_from_chatwoot(self, user: User) -> None:
        """Executa a deleção do usuário no Chatwoot."""
        try:
            us_id = user.user_chatwoot_id
            success = self.client.delete_user(
                user_id=us_id
            )
            if success:
                logger.info(f"Usuário Chatwoot {us_id} deletado com sucesso.")
            else:
                logger.error(f"Falha ao deletar Chatwoot user {us_id}.")
        except ChatwootNotFoundError:
            # Para deleção, se o usuário não for encontrado, consideramos como sucesso
            logger.info(f"User not found in Chatwoot, cleaning up local record for {user}")
    
    @handle_chatwoot_exceptions("add_agent")
    def add_agent(self, user: User) -> Dict[str, Any]:
        try:
            raw_pwd = getattr(user, "_raw_password", None)
            confirmed_at = None
            if raw_pwd:
                # converte o datetime para ISO8601 (sem microssegundos)
                confirmed_at = timezone.now().isoformat(timespec="seconds")
            agent = self.client.create_agent(
                account_id=user.account.chatwoot_account.chatwoot_id,
                name=user.get_full_name() or user.email,
                email=user.email,
                role=user.role,
                password=raw_pwd,
                confirmed_at=confirmed_at,
            )
            if not agent or not agent.get('id'):
                logger.error(f"Failed to create agent for user {user.email}: {agent}")
                return False
            logger.info(f"Agente criado: {agent}")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent for user: {e}")
            return False

    @handle_chatwoot_exceptions("list_agents")
    def get_all_agents(self, account_id: int, user_id: int) -> List[Dict[str, Any]]:
        try:
            """Recupera todos os agentes de uma conta."""
            user = self.client.get_user(user_id)
            if not user or 'access_token' not in user:
                return []
            agents = self.client.list_agents(account_id, access_token=user.get("access_token"))
            if not agents:
                logger.warning(f"No agents found for account {account_id}")
                return []
            logger.info(f"{len(agents)} agentes recuperados para conta {account_id}")
            return agents
        except Exception as e:
            logger.error(f"Failed to get agents for account: {e}")
            return []

    @handle_chatwoot_exceptions("update_agent")
    def update_agent(
        self, 
        account_id: int,
        agent_id: int,
        role: str = None
    ) -> Dict[str, Any]:
        try:
            updated = self.client.update_agent(account_id, agent_id, role)
            if not updated:
                logger.warning(f"Não foi possível atualizar agente {agent_id}")
                return False
            logger.info(f"Agente {agent_id} atualizado: {updated}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            return False

    @handle_chatwoot_exceptions("remove_agent", allow_not_found=True)
    def remove_agent(self, account_id: int, agent_id: int, user_id: int) -> bool:
        try:
            user = self.client.get_user(user_id)
            if not user or 'access_token' not in user:
                return []
            success = self.client.delete_agent(account_id, agent_id, access_token=user.get("access_token"))
            if not success:
                logger.warning(f"Não foi possível remover agente {agent_id}")
                return False
            logger.info(f"Agente {agent_id} removido com sucesso.")
            return success
        except Exception as e:
            logger.error(f"Failed to remove agent: {e}")
            return False
        
    @handle_chatwoot_exceptions("list_inboxes")
    def list_inboxes(
        self,
        account_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all inboxes for the given account.
        GET /api/v1/accounts/{account_id}/inboxes
        """
        try:
            user = self.client.get_user(user_id)
            if not user or 'access_token' not in user:
                return []
            inboxes = self.client.list_inboxes(account_id, access_token=user.get("access_token"))
            logger.info(f"Retrieved {len(inboxes)} inboxes for account {account_id}")
            return inboxes
        except Exception as e:
            logger.error(f"Failed to list inboxes: {e}")
            return []

    @handle_chatwoot_exceptions("create_inbox")
    def create_inbox(
        self,
        account_id: int,
        name: str,
        channel_type: str,
        provider_config: Dict[str, Any],
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new inbox.
        POST /api/v1/accounts/{account_id}/inboxes
        """
        try:
            inbox = self.client.create_inbox(
                account_id=account_id,
                name=name,
                channel_type=channel_type,
                provider_config=provider_config,
                access_token=access_token
            )
            logger.info(f"Created inbox {inbox.get('id')} under account {account_id}")
            return inbox
        except Exception as e:
            logger.error(f"Failed to create inbox: {e}")
            return {}

    @handle_chatwoot_exceptions("update_inbox")
    def update_inbox(
        self,
        account_id: int,
        inbox_id: int,
        name: Optional[str] = None,
        provider_config: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates an existing inbox.
        PATCH /api/v1/accounts/{account_id}/inboxes/{inbox_id}
        """
        try:
            updated = self.client.update_inbox(
                account_id=account_id,
                inbox_id=inbox_id,
                name=name,
                provider_config=provider_config,
                access_token=access_token
            )
            logger.info(f"Updated inbox {inbox_id} under account {account_id}")
            return updated
        except Exception as e:
            logger.error(f"Failed to update inbox: {e}")
            return {}

    @handle_chatwoot_exceptions("delete_inbox", allow_not_found=True)
    def delete_inbox(
        self,
        account_id: int,
        inbox_id: int,
        user_id: int,
    ) -> bool:
        """
        Deletes an inbox.
        DELETE /api/v1/accounts/{account_id}/inboxes/{inbox_id}
        """
        try:
            user = self.client.get_user(user_id)
            if not user or 'access_token' not in user:
                return False
            access_token = user.get("access_token")
            
            success = self.client.delete_inbox(
                account_id=account_id,
                inbox_id=inbox_id,
                access_token=access_token
            )
            if success:
                logger.info(f"Deleted inbox {inbox_id} from account {account_id}")
            else:
                logger.warning(f"Failed to delete inbox {inbox_id} from account {account_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete inbox: {e}")
            return False
