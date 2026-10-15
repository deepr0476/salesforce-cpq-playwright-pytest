from __future__ import annotations

import pytest

from endpoints.account_endpoint import AccountEndpoint
from endpoints.api_client import ApiClient
from endpoints.contact_endpoint import ContactEndpoint
from endpoints.contract_endpoint import ContractEndpoint
from endpoints.opportunity_endpoint import OpportunityEndpoint
from endpoints.order_endpoint import OrderEndpoint
from endpoints.quote_endpoint import QuoteEndpoint
from utils.auth.jwt_auth import JwtAuth


@pytest.fixture(scope="session")
def jwt_auth() -> JwtAuth:
    return JwtAuth()


@pytest.fixture(scope="session")
def api_client(jwt_auth: JwtAuth):
    client = ApiClient(jwt_auth)
    yield client
    client.close()


@pytest.fixture(scope="session")
def account_endpoint(api_client: ApiClient) -> AccountEndpoint:
    return AccountEndpoint(api_client)


@pytest.fixture(scope="session")
def contact_endpoint(api_client: ApiClient) -> ContactEndpoint:
    return ContactEndpoint(api_client)


@pytest.fixture(scope="session")
def opportunity_endpoint(api_client: ApiClient) -> OpportunityEndpoint:
    return OpportunityEndpoint(api_client)


@pytest.fixture(scope="session")
def quote_endpoint(api_client: ApiClient) -> QuoteEndpoint:
    return QuoteEndpoint(api_client)


@pytest.fixture(scope="session")
def order_endpoint(api_client: ApiClient) -> OrderEndpoint:
    return OrderEndpoint(api_client)


@pytest.fixture(scope="session")
def contract_endpoint(api_client: ApiClient) -> ContractEndpoint:
    return ContractEndpoint(api_client)
