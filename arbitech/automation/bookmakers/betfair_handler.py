"""
Betfair Handler

Specialized handler for Betfair exchange with exchange trading, market selection,
and order management capabilities.

Betfair-specific features:
- Exchange betting with back/lay functionality
- Market depth and liquidity information
- Exchange commission calculation
- Market suspension handling
- In-play trading capabilities
"""

import asyncio
import json
import logging
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp

from .handler_base import (
    BaseBookmakerHandler,
    BetRequest,
    BetResponse,
    MarketData,
    SessionInfo,
    OrderStatus,
    HandlerStatus
)


class BetfairHandler(BaseBookmakerHandler):
    """
    Betfair Exchange Handler
    
    Handles Betfair-specific functionality including:
    - Exchange trading with market depth
    - Asian handicap markets
    - In-play betting
    - Commission calculations
    - Market suspensions
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Betfair handler"""
        super().__init__(config)
        
        # Betfair-specific configuration
        self.api_base_url = config.get('api_base_url', 'https://api.betfair.com/exchange/betting/rest/v1')
        self.login_url = config.get('login_url', 'https://identitysso.betfair.com/api/login')
        self.api_key = config.get('api_key', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        
        # Exchange-specific features
        self.exchange_session_token = None
        self.exchange_app_key = config.get('exchange_app_key', 'lwapV6BgqzeNDTJ5')
        self.commission_rate = config.get('commission_rate', 0.02)  # 2% default
        
        # Market tracking
        self.subscribed_markets: Dict[str, Dict[str, Any]] = {}
        self.market_stream_socket = None
        
        # Rate limiting for Betfair API
        self.rate_limiter.update({
            'requests_per_minute': 20,  # Betfair limit
            'requests_per_hour': 1000,
            'requests_per_day': 200000
        })

    def _get_bookmaker_name(self) -> str:
        """Get bookmaker name"""
        return "betfair"

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Betfair-specific authentication headers"""
        headers = {}
        
        if self.session_info.session_token:
            headers['X-Authentication'] = self.session_info.session_token
        
        if self.exchange_app_key:
            headers['X-Application'] = self.exchange_app_key
        
        return headers

    async def authenticate(self) -> bool:
        """Authenticate with Betfair"""
        try:
            self.logger.info("Authenticating with Betfair")
            
            # Step 1: Login to get session token
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Application': self.exchange_app_key,
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.login_url,
                    data=login_data,
                    headers=login_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        login_result = await response.json()
                        
                        if login_result.get('status') == 'SUCCESS':
                            self.session_info.session_token = login_result.get('token')
                            self.session_info.authenticated = True
                            self.session_info.username = self.username
                            
                            # Step 2: Keep session alive
                            await self._keep_session_alive()
                            
                            self.logger.info("Successfully authenticated with Betfair")
                            return True
                        else:
                            self.logger.error(f"Betfair login failed: {login_result.get('detail', 'Unknown error')}")
                            return False
                    else:
                        self.logger.error(f"Betfair login failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error authenticating with Betfair: {e}")
            return False

    async def _keep_session_alive(self) -> None:
        """Keep Betfair session alive"""
        try:
            keepalive_url = "https://identitysso.betfair.com/api/session"
            headers = {
                'X-Authentication': self.session_info.session_token,
                'X-Application': self.exchange_app_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(keepalive_url, headers=headers) as response:
                    if response.status == 200:
                        self.logger.debug("Betfair session kept alive")
                    else:
                        self.logger.warning(f"Failed to keep Betfair session alive: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error keeping Betfair session alive: {e}")

    async def _execute_bet(self, bet_request: BetRequest) -> BetResponse:
        """Execute bet placement on Betfair exchange"""
        try:
            # Convert to Betfair format
            betfair_request = self._convert_to_betfair_format(bet_request)
            
            # Place bet
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/orders/',
                data=betfair_request
            )
            
            if response.get('status') == 'SUCCESS':
                instructions = response.get('instructionReports', [])
                if instructions:
                    instruction = instructions[0]
                    bet_id = instruction.get('betId')
                    
                    return BetResponse(
                        success=True,
                        bet_id=bet_id,
                        status=OrderStatus.SUBMITTED,
                        odds=bet_request.odds,
                        stake=bet_request.stake,
                        metadata={'exchange_status': 'PLACED'}
                    )
            
            return BetResponse(
                success=False,
                error_message=response.get('errorDetails', 'Unknown error')
            )
            
        except Exception as e:
            self.logger.error(f"Error executing bet on Betfair: {e}")
            return BetResponse(
                success=False,
                error_message=str(e)
            )

    def _convert_to_betfair_format(self, bet_request: BetRequest) -> Dict[str, Any]:
        """Convert standard bet request to Betfair format"""
        betfair_request = {
            'marketId': bet_request.market_id,
            'instructions': [
                {
                    'actionType': 'PLACE',
                    'selectionId': bet_request.selection_id,
                    'side': bet_request.bet_type.upper(),  # BACK or LAY
                    'limitOrder': {
                        'size': str(bet_request.stake),
                        'price': str(bet_request.odds)
                    }
                }
            ]
        }
        
        # Add market type specific parameters
        if bet_request.market_type == 'asian_handicap':
            handicap = bet_request.metadata.get('handicap')
            if handicap:
                betfair_request['instructions'][0]['handicap'] = handicap
        
        return betfair_request

    async def _fetch_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch available markets from Betfair"""
        try:
            # Get available events
            events_response = await self._make_request(
                'POST',
                f'{self.api_base_url}/listEvents/',
                data={'filter': self._build_event_filter(filters)}
            )
            
            markets = []
            for event in events_response.get('events', []):
                market_data = await self._get_event_markets(event['event']['id'])
                markets.extend(market_data)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching Betfair markets: {e}")
            return []

    def _build_event_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Betfair event filter"""
        event_filter = {
            'eventTypeIds': filters.get('event_types', [1]),  # 1 = Football
            'maxResults': filters.get('max_results', 200)
        }
        
        # Add time range
        if 'from_date' in filters:
            event_filter['fromDate'] = filters['from_date']
        if 'to_date' in filters:
            event_filter['toDate'] = filters['to_date']
        
        # Add country codes
        if 'countries' in filters:
            event_filter['competitionIds'] = filters['countries']
        
        return event_filter

    async def _get_event_markets(self, event_id: str) -> List[MarketData]:
        """Get markets for a specific event"""
        try:
            markets_response = await self._make_request(
                'POST',
                f'{self.api_base_url}/listMarkets/',
                data={
                    'eventIds': [event_id],
                    'maxResults': 50
                }
            )
            
            markets = []
            for market in markets_response.get('markets', []):
                # Get market selections
                selections = await self._get_market_selections(market['marketId'])
                
                betfair_market = MarketData(
                    market_id=market['marketId'],
                    event_id=event_id,
                    event_name=market.get('event', {}).get('name', ''),
                    market_type=market.get('marketType', 'match_odds'),
                    selections=selections,
                    suspended=market.get('status') == 'SUSPENDED',
                    metadata={
                        'betfair': {
                            'total_matched': market.get('totalMatched', 0),
                            'runners': market.get('numberOfRunners', 0),
                            'exchange_type': 'betting_exchange'
                        }
                    }
                )
                
                markets.append(betfair_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error getting event markets: {e}")
            return []

    async def _get_market_selections(self, market_id: str) -> List[Dict[str, Any]]:
        """Get selections for a market"""
        try:
            selections_response = await self._make_request(
                'POST',
                f'{self.api_base_url}/listMarketBook/',
                data={
                    'marketIds': [market_id],
                    'priceProjection': {
                        'priceData': ['EX_BEST_OFFERS', 'EX_TRADED']
                    }
                }
            )
            
            selections = []
            if selections_response.get('marketBooks'):
                market_book = selections_response['marketBooks'][0]
                
                for runner in market_book.get('runners', []):
                    selection = {
                        'selection_id': runner['selectionId'],
                        'status': runner['status'],
                        'handicap': runner.get('handicap', 0),
                        'exchange': {
                            'back': runner.get('ex', {}).get('availableToBack', []),
                            'lay': runner.get('ex', {}).get('availableToLay', []),
                            'traded_volume': runner.get('ex', {}).get('tradedVolume', [])
                        }
                    }
                    selections.append(selection)
            
            return selections
            
        except Exception as e:
            self.logger.error(f"Error getting market selections: {e}")
            return []

    async def _fetch_odds(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific market"""
        try:
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/listMarketBook/',
                data={
                    'marketIds': [market_id],
                    'priceProjection': {
                        'priceData': ['EX_BEST_OFFERS', 'EX_TRADED']
                    }
                }
            )
            
            if response.get('marketBooks'):
                return response['marketBooks'][0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching odds for market {market_id}: {e}")
            return None

    async def _execute_cancel(self, bet_id: str) -> bool:
        """Cancel bet on Betfair"""
        try:
            cancel_request = {
                'marketId': self._get_market_id_from_bet(bet_id),
                'instructions': [
                    {
                        'actionType': 'CANCEL',
                        'betId': bet_id
                    }
                ]
            }
            
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/orders/',
                data=cancel_request
            )
            
            return response.get('status') == 'SUCCESS'
            
        except Exception as e:
            self.logger.error(f"Error cancelling bet {bet_id}: {e}")
            return False

    def _get_market_id_from_bet(self, bet_id: str) -> str:
        """Extract market ID from bet ID (placeholder implementation)"""
        # In reality, you'd need to store or retrieve this mapping
        return "1.23"

    async def _finalize_initialization(self) -> bool:
        """Finalize Betfair-specific initialization"""
        # Get account info
        account_info = await self.get_account_info()
        if account_info:
            self.session_info.balance = account_info.get('availableBalance', 0)
            self.session_info.currency = account_info.get('currencyCode', 'GBP')
            return True
        return False

    def get_supported_markets(self) -> List[str]:
        """Get Betfair-supported market types"""
        return [
            'match_odds',
            'asian_handicap',
            'over_under',
            'correct_score',
            'first_goal_scorer',
            'half_time_result',
            'both_teams_to_score',
            'corners',
            'cards',
            'player_stats'
        ]

    async def get_balance(self) -> Optional[float]:
        """Get Betfair account balance"""
        try:
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/getAccountFunds/'
            )
            
            return response.get('availableBalance')
            
        except Exception as e:
            self.logger.error(f"Error getting Betfair balance: {e}")
            return None

    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed Betfair account information"""
        try:
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/getAccount/'
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting Betfair account info: {e}")
            return {}

    async def get_bet_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get Betfair betting history"""
        try:
            # Note: Betfair's getM bets is deprecated, this is a placeholder
            # In reality, you'd use account statements
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting Betfair bet history: {e}")
            return []

    async def update_market_data(self, market_id: str) -> Optional[MarketData]:
        """Update market data for a specific market"""
        try:
            odds_data = await self._fetch_odds(market_id)
            if not odds_data:
                return None
            
            # Convert to standard format
            market = MarketData(
                market_id=market_id,
                event_id=odds_data.get('marketId', ''),
                event_name='',
                market_type='match_odds',
                selections=[],
                suspended=odds_data.get('status') == 'SUSPENDED'
            )
            
            for runner in odds_data.get('runners', []):
                selection = {
                    'selection_id': runner['selectionId'],
                    'status': runner['status'],
                    'handicap': runner.get('handicap', 0),
                    'exchange': {
                        'back': runner.get('ex', {}).get('availableToBack', []),
                        'lay': runner.get('ex', {}).get('availableToLay', []),
                        'traded_volume': runner.get('ex', {}).get('tradedVolume', [])
                    }
                }
                market.selections.append(selection)
            
            return market
            
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
            return None

    # Betfair-specific methods
    async def get_market_profit_and_loss(self, market_id: str) -> Dict[str, Any]:
        """Get market profit and loss information"""
        try:
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/getMarketProfitAndLoss/',
                data={'marketIds': [market_id]}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting P&L for market {market_id}: {e}")
            return {}

    async def get_account_statement(self, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        """Get account statement for date range"""
        try:
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/getAccountStatement/',
                data={
                    'fromDate': from_date.isoformat(),
                    'toDate': to_date.isoformat(),
                    'itemsPerPage': 100
                }
            )
            
            return response.get('accountStatement', [])
            
        except Exception as e:
            self.logger.error(f"Error getting account statement: {e}")
            return []

    def calculate_commission(self, stake: float, odds: float, profit: float = None) -> float:
        """Calculate Betfair commission on net winnings"""
        if profit is None:
            profit = stake * (odds - 1)
        
        return max(0, profit * self.commission_rate)

    def get_best_price(self, selection_data: Dict[str, Any], side: str = 'back') -> Optional[Tuple[float, float]]:
        """Get best available price and size for a selection"""
        exchange_data = selection_data.get('exchange', {})
        prices = exchange_data.get(side, [])
        
        if prices:
            best_price = prices[0]  # First price is the best
            return best_price.get('price'), best_price.get('size')
        
        return None, None

    async def subscribe_to_market(self, market_id: str) -> bool:
        """Subscribe to market updates via streaming API"""
        try:
            # In a full implementation, this would connect to Betfair's streaming API
            # For now, we'll track subscription state
            self.subscribed_markets[market_id] = {
                'subscribed_at': time.time(),
                'active': True
            }
            self.logger.info(f"Subscribed to market {market_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to market {market_id}: {e}")
            return False

    async def unsubscribe_from_market(self, market_id: str) -> bool:
        """Unsubscribe from market updates"""
        try:
            if market_id in self.subscribed_markets:
                self.subscribed_markets[market_id]['active'] = False
                del self.subscribed_markets[market_id]
                self.logger.info(f"Unsubscribed from market {market_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from market {market_id}: {e}")
            return False

    async def _perform_health_check(self) -> bool:
        """Perform Betfair-specific health check"""
        try:
            # Test session
            await self._keep_session_alive()
            return True
        except:
            return False