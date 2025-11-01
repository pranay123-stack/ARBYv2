"""
Pinnacle Handler

Specialized handler for Pinnacle with Asian handicap markets, live betting,
and stake management capabilities.

Pinnacle-specific features:
- Asian handicap markets
- Live/in-play betting
- High stake limits
- Low margins
- Multiple currencies
- esports betting
"""

import asyncio
import json
import logging
import time
import base64
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


class PinnacleHandler(BaseBookmakerHandler):
    """
    Pinnacle Sports Handler
    
    Handles Pinnacle-specific functionality including:
    - Asian handicap betting
    - Live betting markets
    - High stake limits
    - esports betting
    - Multiple currency support
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Pinnacle handler"""
        super().__init__(config)
        
        # Pinnacle-specific configuration
        self.api_base_url = config.get('api_base_url', 'https://api.pinnacle.com')
        self.login_url = config.get('login_url', 'https://api.pinnacle.com/oauth2/token')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        
        # OAuth tokens
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # Supported currencies
        self.supported_currencies = config.get('supported_currencies', ['USD', 'EUR', 'GBP', 'AUD'])
        self.default_currency = config.get('default_currency', 'USD')
        
        # Live betting
        self.live_markets: Dict[str, Dict[str, Any]] = {}
        self.live_betting_enabled = config.get('live_betting_enabled', True)
        
        # Rate limiting for Pinnacle API
        self.rate_limiter.update({
            'requests_per_minute': 300,  # Pinnacle limit
            'requests_per_hour': 10000
        })

    def _get_bookmaker_name(self) -> str:
        """Get bookmaker name"""
        return "pinnacle"

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Pinnacle-specific authentication headers"""
        headers = {}
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        
        return headers

    async def authenticate(self) -> bool:
        """Authenticate with Pinnacle"""
        try:
            self.logger.info("Authenticating with Pinnacle")
            
            # OAuth2 authentication
            auth_string = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            auth_headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            auth_data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.login_url,
                    data=auth_data,
                    headers=auth_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        auth_result = await response.json()
                        
                        self.access_token = auth_result.get('access_token')
                        self.refresh_token = auth_result.get('refresh_token')
                        expires_in = auth_result.get('expires_in', 3600)
                        
                        self.token_expires_at = time.time() + expires_in - 60  # 60s buffer
                        self.session_info.session_token = self.access_token
                        self.session_info.authenticated = True
                        self.session_info.username = self.username
                        
                        self.logger.info("Successfully authenticated with Pinnacle")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Pinnacle authentication failed: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error authenticating with Pinnacle: {e}")
            return False

    async def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        try:
            auth_string = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            auth_headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            auth_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.login_url,
                    data=auth_data,
                    headers=auth_headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        auth_result = await response.json()
                        
                        self.access_token = auth_result.get('access_token')
                        self.refresh_token = auth_result.get('refresh_token', self.refresh_token)
                        expires_in = auth_result.get('expires_in', 3600)
                        
                        self.token_expires_at = time.time() + expires_in - 60
                        self.session_info.session_token = self.access_token
                        
                        self.logger.debug("Pinnacle token refreshed successfully")
                        return True
                    else:
                        self.logger.error("Failed to refresh Pinnacle token")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error refreshing Pinnacle token: {e}")
            return False

    async def _ensure_valid_token(self) -> None:
        """Ensure access token is valid, refresh if needed"""
        if not self.access_token or time.time() >= self.token_expires_at:
            if not await self._refresh_access_token():
                # If refresh fails, try full authentication
                await self.authenticate()

    async def _execute_bet(self, bet_request: BetRequest) -> BetResponse:
        """Execute bet placement on Pinnacle"""
        try:
            await self._ensure_valid_token()
            
            # Convert to Pinnacle format
            pinnacle_request = self._convert_to_pinnacle_format(bet_request)
            
            # Place bet
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/v1/bets/straight',
                data=pinnacle_request
            )
            
            if 'id' in response:  # Success response has bet ID
                bet_id = str(response['id'])
                
                # Get bet status
                bet_status = await self._get_bet_status(bet_id)
                
                return BetResponse(
                    success=True,
                    bet_id=bet_id,
                    status=self._map_pinnacle_status(bet_status.get('status', 'PENDING')),
                    odds=bet_request.odds,
                    stake=bet_request.stake,
                    metadata={'pinnacle': bet_status}
                )
            
            return BetResponse(
                success=False,
                error_message=response.get('message', 'Unknown error')
            )
            
        except Exception as e:
            self.logger.error(f"Error executing bet on Pinnacle: {e}")
            return BetResponse(
                success=False,
                error_message=str(e)
            )

    def _convert_to_pinnacle_format(self, bet_request: BetRequest) -> Dict[str, Any]:
        """Convert standard bet request to Pinnacle format"""
        pinnacle_request = {
            'uniqueRequestId': f"{int(time.time() * 1000000)}",
            'sportId': self._get_sport_id_from_market_type(bet_request.market_type),
            'eventId': int(bet_request.event_id) if bet_request.event_id else 0,
            'marketId': int(bet_request.market_id),
            'periodNumber': 0,  # Default to full match
            'line': self._calculate_line(bet_request),  # For Asian handicaps
            'betType': 'MONEYLINE' if bet_request.bet_type == 'back' else 'SPREAD',
            'side': 'ISLANDER' if bet_request.bet_type == 'back' else 'UNDERDOG',
            'oddsFormat': 'DECIMAL',
            'stake': bet_request.stake
        }
        
        # Add Asian handicap information if applicable
        if bet_request.market_type == 'asian_handicap':
            handicap = bet_request.metadata.get('handicap', 0)
            pinnacle_request['line'] = handicap
            pinnacle_request['betType'] = 'SPREAD'
        
        return pinnacle_request

    def _get_sport_id_from_market_type(self, market_type: str) -> int:
        """Get Pinnacle sport ID from market type"""
        sport_mapping = {
            'match_odds': 1,  # Football
            'asian_handicap': 1,
            'over_under': 1,
            'correct_score': 1,
            'esports_match_odds': 18,  # Esports
            'esports_asia_handicap': 18
        }
        return sport_mapping.get(market_type, 1)  # Default to football

    def _calculate_line(self, bet_request: BetRequest) -> float:
        """Calculate line for Asian handicap markets"""
        if bet_request.market_type == 'asian_handicap':
            return bet_request.metadata.get('handicap', 0)
        elif bet_request.market_type == 'over_under':
            return bet_request.metadata.get('line', 2.5)
        return 0.0

    def _map_pinnacle_status(self, pinnacle_status: str) -> OrderStatus:
        """Map Pinnacle status to standard status"""
        status_mapping = {
            'PENDING': OrderStatus.PENDING,
            'PROCESSING': OrderStatus.SUBMITTED,
            'ACCEPTED': OrderStatus.ACCEPTED,
            'REJECTED': OrderStatus.REJECTED,
            'CANCELLED': OrderStatus.CANCELLED,
            'LATE_BET_CANCELLED': OrderStatus.CANCELLED,
            'LATE_BET_ACCEPTED': OrderStatus.ACCEPTED
        }
        return status_mapping.get(pinnacle_status, OrderStatus.PENDING)

    async def _fetch_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch available markets from Pinnacle"""
        try:
            await self._ensure_valid_token()
            
            markets = []
            
            # Get live markets if enabled
            if self.live_betting_enabled:
                live_markets = await self._fetch_live_markets()
                markets.extend(live_markets)
            
            # Get upcoming markets
            upcoming_markets = await self._fetch_upcoming_markets(filters)
            markets.extend(upcoming_markets)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching Pinnacle markets: {e}")
            return []

    async def _fetch_live_markets(self) -> List[MarketData]:
        """Fetch live markets from Pinnacle"""
        try:
            live_markets = []
            
            for sport_id in [1, 18]:  # Football and Esports
                response = await self._make_request(
                    'GET',
                    f'{self.api_base_url}/v1/odds?sportId={sport_id}&oddsFormat=Decimal&market='
                )
                
                if 'leagues' in response:
                    for league in response['leagues']:
                        for event in league.get('events', []):
                            # Get event details
                            event_details = await self._get_event_details(event['id'])
                            
                            for period in event_details.get('periods', []):
                                for market in period.get('prices', []):
                                    pinnacle_market = await self._convert_pinnacle_market_to_standard(
                                        market, event, period
                                    )
                                    if pinnacle_market:
                                        live_markets.append(pinnacle_market)
                                        self.live_markets[market['id']] = {
                                            'event_id': event['id'],
                                            'sport_id': sport_id,
                                            'last_update': time.time()
                                        }
            
            return live_markets
            
        except Exception as e:
            self.logger.error(f"Error fetching live markets: {e}")
            return []

    async def _fetch_upcoming_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch upcoming markets from Pinnacle"""
        try:
            upcoming_markets = []
            
            sport_id = filters.get('sport_id', 1)
            
            # Get fixtures for today
            today = datetime.now().strftime('%Y-%m-%d')
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/fixtures?sportId={sport_id}&leagues=&fromDate={today}&toDate={today}'
            )
            
            if 'leagues' in response:
                for league in response['leagues']:
                    for event in league.get('events', []):
                        # Get event details
                        event_details = await self._get_event_details(event['id'])
                        
                        for period in event_details.get('periods', []):
                            for market in period.get('prices', []):
                                pinnacle_market = await self._convert_pinnacle_market_to_standard(
                                    market, event, period
                                )
                                if pinnacle_market:
                                    upcoming_markets.append(pinnacle_market)
            
            return upcoming_markets
            
        except Exception as e:
            self.logger.error(f"Error fetching upcoming markets: {e}")
            return []

    async def _get_event_details(self, event_id: int) -> Dict[str, Any]:
        """Get detailed event information from Pinnacle"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/events/{event_id}?oddsFormat=Decimal&market='
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting event details: {e}")
            return {}

    async def _convert_pinnacle_market_to_standard(
        self, 
        market: Dict[str, Any], 
        event: Dict[str, Any], 
        period: Dict[str, Any]
    ) -> Optional[MarketData]:
        """Convert Pinnacle market data to standard format"""
        try:
            selections = []
            
            for price in market.get('prices', []):
                selection = {
                    'selection_id': str(price['designator']),
                    'name': price.get('designator'),
                    'odds': price.get('odds', 0),
                    'line': price.get('line'),
                    'pinnacle': {
                        'price_id': price['id'],
                        'max_stake': price.get('maxStake'),
                        'min_stake': price.get('minStake')
                    }
                }
                selections.append(selection)
            
            standard_market = MarketData(
                market_id=str(market['id']),
                event_id=str(event['id']),
                event_name=event.get('name', ''),
                market_type=self._map_market_type(market.get('type', 'MONEYLINE')),
                selections=selections,
                metadata={
                    'pinnacle': {
                        'league': event.get('league'),
                        'sport': event.get('sport'),
                        'period': period.get('number'),
                        'period_desc': period.get('description'),
                        'status': event.get('status'),
                        'is_live': event.get('isLive', False)
                    }
                }
            )
            
            return standard_market
            
        except Exception as e:
            self.logger.error(f"Error converting Pinnacle market: {e}")
            return None

    def _map_market_type(self, pinnacle_market_type: str) -> str:
        """Map Pinnacle market type to standard type"""
        type_mapping = {
            'MONEYLINE': 'match_odds',
            'SPREAD': 'asian_handicap',
            'TOTAL': 'over_under',
            'TEAM_TOTAL': 'team_total'
        }
        return type_mapping.get(pinnacle_market_type, 'match_odds')

    async def _fetch_odds(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific market"""
        try:
            await self._ensure_valid_token()
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/odds?sportId=1&oddsFormat=Decimal&market={market_id}'
            )
            
            # Extract market data from response
            if 'leagues' in response:
                for league in response['leagues']:
                    for event in league.get('events', []):
                        event_details = await self._get_event_details(int(event['id']))
                        
                        for period in event_details.get('periods', []):
                            for market in period.get('prices', []):
                                if str(market['id']) == market_id:
                                    return {
                                        'market': market,
                                        'event': event,
                                        'period': period
                                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching odds for market {market_id}: {e}")
            return None

    async def _execute_cancel(self, bet_id: str) -> bool:
        """Cancel bet on Pinnacle"""
        try:
            await self._ensure_valid_token()
            
            # Note: Pinnacle may not support bet cancellation for straight bets
            # This is a placeholder implementation
            self.logger.warning("Pinnacle doesn't support bet cancellation for straight bets")
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling bet {bet_id}: {e}")
            return False

    async def _get_bet_status(self, bet_id: str) -> Dict[str, Any]:
        """Get status of a specific bet"""
        try:
            await self._ensure_valid_token()
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/bets/{bet_id}'
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting bet status: {e}")
            return {}

    async def _finalize_initialization(self) -> bool:
        """Finalize Pinnacle-specific initialization"""
        # Get account info
        account_info = await self.get_account_info()
        if account_info and 'currency' in account_info:
            self.session_info.balance = account_info.get('balanceAvailable', 0)
            self.session_info.currency = account_info.get('currency', self.default_currency)
            return True
        return False

    def get_supported_markets(self) -> List[str]:
        """Get Pinnacle-supported market types"""
        return [
            'match_odds',
            'asian_handicap',
            'over_under',
            'correct_score',
            'first_period',
            'second_period',
            'esports_match_odds',
            'esports_asia_handicap',
            'team_total'
        ]

    async def get_balance(self) -> Optional[float]:
        """Get Pinnacle account balance"""
        try:
            await self._ensure_valid_token()
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/client/balance'
            )
            
            return response.get('availableBalance')
            
        except Exception as e:
            self.logger.error(f"Error getting Pinnacle balance: {e}")
            return None

    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed Pinnacle account information"""
        try:
            await self._ensure_valid_token()
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/client/balance'
            )
            
            return {
                'currency': self.default_currency,
                'balanceAvailable': response.get('availableBalance'),
                'balancePending': response.get('balancePending'),
                'lastUpdate': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Pinnacle account info: {e}")
            return {}

    async def get_bet_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get Pinnacle betting history"""
        try:
            await self._ensure_valid_token()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/bets/settledbet?' 
                f'fromDate={start_date.strftime("%Y-%m-%d")}&'
                f'toDate={end_date.strftime("%Y-%m-%d")}'
            )
            
            return response.get('bets', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Pinnacle bet history: {e}")
            return []

    async def update_market_data(self, market_id: str) -> Optional[MarketData]:
        """Update market data for a specific market"""
        try:
            odds_data = await self._fetch_odds(market_id)
            if not odds_data:
                return None
            
            # Convert to standard format
            return await self._convert_pinnacle_market_to_standard(
                odds_data['market'],
                odds_data['event'],
                odds_data['period']
            )
            
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
            return None

    # Pinnacle-specific methods
    async def get_live_markets(self, sport_id: int = 1) -> List[Dict[str, Any]]:
        """Get all live markets for a sport"""
        try:
            await self._ensure_valid_token()
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/odds?sportId={sport_id}&oddsFormat=Decimal&market='
            )
            
            return response.get('leagues', [])
            
        except Exception as e:
            self.logger.error(f"Error getting live markets: {e}")
            return []

    async def get_esports_markets(self) -> List[MarketData]:
        """Get esports markets from Pinnacle"""
        try:
            return await self._fetch_upcoming_markets({'sport_id': 18})
            
        except Exception as e:
            self.logger.error(f"Error getting esports markets: {e}")
            return []

    def calculate_asian_handicap_outcome(
        self,
        home_score: float,
        away_score: float,
        handicap: float,
        bet_type: str
    ) -> str:
        """Calculate Asian handicap outcome"""
        adjusted_home = home_score + handicap
        adjusted_away = away_score
        
        if bet_type == 'home':
            if adjusted_home > adjusted_away:
                return 'win'
            elif adjusted_home == adjusted_away:
                return 'push'
            else:
                return 'loss'
        elif bet_type == 'away':
            if adjusted_away > adjusted_home:
                return 'win'
            elif adjusted_away == adjusted_home:
                return 'push'
            else:
                return 'loss'
        
        return 'unknown'

    def get_max_stake(self, market_data: Dict[str, Any], odds: float) -> float:
        """Get maximum stake for a market"""
        for selection in market_data.get('selections', []):
            if selection.get('odds') == odds:
                return selection.get('pinnacle', {}).get('max_stake', 0)
        return 0

    async def _perform_health_check(self) -> bool:
        """Perform Pinnacle-specific health check"""
        try:
            await self._ensure_valid_token()
            return True
        except:
            return False