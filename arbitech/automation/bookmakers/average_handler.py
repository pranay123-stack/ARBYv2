"""
Aver Handler

Specialized handler for Aver with regional markets and local payment methods.

Aver-specific features:
- Regional sports betting markets
- Local payment methods
- Multi-currency support
- Regional compliance
- Mobile-first interface
- Live streaming integration
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


class AverHandler(BaseBookmakerHandler):
    """
    Aver Regional Sports Betting Handler
    
    Handles Aver-specific functionality including:
    - Regional market focus (Africa, Asia, Latin America)
    - Local payment methods
    - Mobile-first betting interface
    - Live streaming integration
    - Regional sports coverage
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Aver handler"""
        super().__init__(config)
        
        # Aver-specific configuration
        self.api_base_url = config.get('api_base_url', 'https://api.aver.com')
        self.login_url = config.get('login_url', 'https://auth.aver.com/login')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.api_key = config.get('api_key', '')
        
        # Regional settings
        self.region = config.get('region', 'africa')  # africa, asia, latam
        self.language = config.get('language', 'en')
        self.timezone = config.get('timezone', 'Africa/Johannesburg')
        
        # Supported local payment methods
        self.local_payment_methods = config.get('local_payment_methods', {
            'africa': ['mtn_mobile_money', 'vodafone_cash', 'orange_money', 'airtel_money', 'bank_transfer'],
            'asia': ['alipay', 'wechat_pay', 'line_pay', 'gcash', 'paytm', 'bank_transfer'],
            'latam': ['pix', 'mercadopago', 'oca', 'rapipago', 'sodexo', 'bank_transfer']
        })
        
        # Supported currencies for region
        self.supported_currencies = config.get('supported_currencies', {
            'africa': ['GHS', 'NGN', 'KES', 'UGX', 'ZAR', 'USD'],
            'asia': ['CNY', 'JPY', 'KRW', 'THB', 'INR', 'PHP', 'USD'],
            'latam': ['BRL', 'MXN', 'ARS', 'CLP', 'COP', 'USD']
        })
        self.default_currency = config.get('default_currency', 'USD')
        
        # Live streaming integration
        self.live_stream_enabled = config.get('live_stream_enabled', True)
        self.stream_api_url = config.get('stream_api_url', 'https://stream.aver.com')
        
        # Mobile interface optimization
        self.mobile_optimized = config.get('mobile_optimized', True)
        
        # Rate limiting for Aver API
        self.rate_limiter.update({
            'requests_per_minute': 200,
            'requests_per_hour': 5000
        })

    def _get_bookmaker_name(self) -> str:
        """Get bookmaker name"""
        return "aver"

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Aver-specific authentication headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Region': self.region,
            'X-Language': self.language,
            'X-Timezone': self.timezone
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        if self.session_info.session_token:
            headers['X-Session-Token'] = self.session_info.session_token
        
        return headers

    async def authenticate(self) -> bool:
        """Authenticate with Aver"""
        try:
            self.logger.info(f"Authenticating with Aver ({self.region} region)")
            
            # Login with credentials
            auth_data = {
                'username': self.username,
                'password': self.password,
                'region': self.region,
                'language': self.language
            }
            
            auth_headers = {
                'Content-Type': 'application/json',
                'X-Region': self.region,
                'X-Language': self.language
            }
            
            if self.api_key:
                auth_headers['Authorization'] = f'Bearer {self.api_key}'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.login_url,
                    json=auth_data,
                    headers=auth_headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        auth_result = await response.json()
                        
                        if auth_result.get('success', False):
                            self.session_info.session_token = auth_result.get('sessionToken')
                            self.session_info.authenticated = True
                            self.session_info.username = self.username
                            self.session_info.user_id = auth_result.get('userId')
                            
                            # Get region-specific account info
                            await self._initialize_regional_settings()
                            
                            self.logger.info(f"Successfully authenticated with Aver ({self.region})")
                            return True
                        else:
                            self.logger.error(f"Aver login failed: {auth_result.get('message', 'Unknown error')}")
                            return False
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Aver authentication failed: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error authenticating with Aver: {e}")
            return False

    async def _initialize_regional_settings(self) -> None:
        """Initialize region-specific settings"""
        try:
            # Get supported payment methods for region
            self.supported_currencies = self.supported_currencies.get(self.region, ['USD'])
            
            # Set default currency based on region
            if self.region == 'africa' and 'GHS' in self.supported_currencies:
                self.default_currency = 'GHS'
            elif self.region == 'asia' and 'CNY' in self.supported_currencies:
                self.default_currency = 'CNY'
            elif self.region == 'latam' and 'BRL' in self.supported_currencies:
                self.default_currency = 'BRL'
            
            self.logger.info(f"Regional settings initialized for {self.region}")
            
        except Exception as e:
            self.logger.error(f"Error initializing regional settings: {e}")

    async def _execute_bet(self, bet_request: BetRequest) -> BetResponse:
        """Execute bet placement on Aver"""
        try:
            # Convert to Aver format
            aver_request = self._convert_to_aver_format(bet_request)
            
            # Place bet via API
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/v1/bets',
                data=aver_request
            )
            
            if response.get('success', False):
                bet_id = response.get('betId')
                
                return BetResponse(
                    success=True,
                    bet_id=bet_id,
                    status=self._map_aver_status(response.get('status', 'PENDING')),
                    odds=bet_request.odds,
                    stake=bet_request.stake,
                    metadata={
                        'aver': {
                            'region': self.region,
                            'currency': aver_request.get('currency'),
                            'payment_method': aver_request.get('paymentMethod'),
                            'mobile_bet': aver_request.get('mobileBet', False)
                        }
                    }
                )
            
            return BetResponse(
                success=False,
                error_message=response.get('message', 'Unknown error')
            )
            
        except Exception as e:
            self.logger.error(f"Error executing bet on Aver: {e}")
            return BetResponse(
                success=False,
                error_message=str(e)
            )

    def _convert_to_aver_format(self, bet_request: BetRequest) -> Dict[str, Any]:
        """Convert standard bet request to Aver format"""
        aver_request = {
            'marketId': bet_request.market_id,
            'selectionId': bet_request.selection_id,
            'odds': bet_request.odds,
            'stake': bet_request.stake,
            'currency': self.default_currency,
            'betType': bet_request.bet_type.upper(),
            'region': self.region,
            'language': self.language,
            'timestamp': int(time.time()),
            'mobileBet': self.mobile_optimized,
            'metadata': {
                'eventId': bet_request.event_id,
                'eventName': bet_request.event_name,
                'marketType': bet_request.market_type,
                'original_metadata': bet_request.metadata
            }
        }
        
        # Add regional-specific betting options
        if self.region == 'africa':
            aver_request['paymentMethod'] = 'mobile_money'  # Default for Africa
            aver_request['localTime'] = True
            if bet_request.market_type == 'premier_league':
                aver_request['enhancedOdds'] = True
        
        elif self.region == 'asia':
            aver_request['paymentMethod'] = 'alipay'  # Default for Asia
            aver_request['cashOutEnabled'] = True
            if bet_request.market_type == 'asian_cup':
                aver_request['specialMarkets'] = True
        
        elif self.region == 'latam':
            aver_request['paymentMethod'] = 'pix'  # Default for LATAM
            aver_request['liveStreaming'] = self.live_stream_enabled
            if bet_request.market_type == 'copa_libertadores':
                aver_request['regionalBoost'] = True
        
        # Add mobile-optimized features
        if self.mobile_optimized:
            aver_request['quickBet'] = bet_request.stake <= 10
            aver_request['favorites'] = bet_request.metadata.get('favorite', False)
        
        return aver_request

    def _map_aver_status(self, aver_status: str) -> OrderStatus:
        """Map Aver status to standard status"""
        status_mapping = {
            'PENDING': OrderStatus.PENDING,
            'CONFIRMED': OrderStatus.SUBMITTED,
            'ACCEPTED': OrderStatus.ACCEPTED,
            'REJECTED': OrderStatus.REJECTED,
            'CANCELLED': OrderStatus.CANCELLED,
            'PARTIAL': OrderStatus.PARTIAL,
            'SETTLED': OrderStatus.FILLED,
            'VOIDED': OrderStatus.CANCELLED
        }
        return status_mapping.get(aver_status, OrderStatus.PENDING)

    async def _fetch_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch available markets from Aver"""
        try:
            markets = []
            
            # Get regional sports markets
            sports_markets = await self._fetch_regional_sports_markets(filters)
            markets.extend(sports_markets)
            
            # Get local league markets
            if filters.get('include_local_leagues', True):
                local_markets = await self._fetch_local_league_markets()
                markets.extend(local_markets)
            
            # Get live markets if enabled
            if self.live_stream_enabled and filters.get('include_live', False):
                live_markets = await self._fetch_live_markets_with_stream()
                markets.extend(live_markets)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching Aver markets: {e}")
            return []

    async def _fetch_regional_sports_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch regional sports betting markets"""
        try:
            # Build region-specific query parameters
            params = {
                'region': self.region,
                'language': self.language,
                'currency': self.default_currency,
                'sports': self._get_regional_sports_list()
            }
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/sports',
                params=params
            )
            
            markets = []
            for market_data in response.get('markets', []):
                aver_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['eventId'],
                    event_name=market_data['eventName'],
                    market_type=market_data.get('type', 'match_odds'),
                    selections=market_data.get('selections', []),
                    metadata={
                        'aver': {
                            'region': self.region,
                            'league': market_data.get('league'),
                            'local_start_time': market_data.get('localStartTime'),
                            'currency': market_data.get('currency'),
                            'streaming_available': market_data.get('streamingAvailable', False),
                            'enhanced_odds': market_data.get('enhancedOdds', False),
                            'mobile_optimized': market_data.get('mobileOptimized', False)
                        }
                    }
                )
                markets.append(aver_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching regional sports markets: {e}")
            return []

    def _get_regional_sports_list(self) -> List[str]:
        """Get list of popular sports for the region"""
        regional_sports = {
            'africa': ['football', 'basketball', 'rugby', 'cricket', 'athletics'],
            'asia': ['football', 'table_tennis', 'badminton', 'esports', 'basketball'],
            'latam': ['football', 'basketball', 'volleyball', 'tennis', 'rugby']
        }
        return regional_sports.get(self.region, ['football'])

    async def _fetch_local_league_markets(self) -> List[MarketData]:
        """Fetch local league markets"""
        try:
            params = {
                'region': self.region,
                'league': self._get_local_leagues(),
                'localOnly': True
            }
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/local-leagues',
                params=params
            )
            
            markets = []
            for market_data in response.get('markets', []):
                aver_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['eventId'],
                    event_name=market_data['eventName'],
                    market_type=market_data.get('type', 'match_odds'),
                    selections=market_data.get('selections', []),
                    metadata={
                        'aver': {
                            'region': self.region,
                            'league_type': 'local',
                            'local_relevance': market_data.get('localRelevance', 0),
                            'community_betting': market_data.get('communityBetting', False)
                        }
                    }
                )
                markets.append(aver_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching local league markets: {e}")
            return []

    def _get_local_leagues(self) -> List[str]:
        """Get local leagues for the region"""
        local_leagues = {
            'africa': [
                'english_premier_league', 'uefa_champions_league',
                'caf_champions_league', 'nigeria_professional_league',
                'south_african_premier_soccer_league', 'egyptian_premier_league'
            ],
            'asia': [
                'j1_league', 'k_league', 'chinese_super_league',
                'india_super_league', 'philippines_football_league'
            ],
            'latam': [
                'brazilian_serie_a', 'argentina_primera_division',
                'mexican_liga_mx', 'copa_libertadores', 'copa_sudamericana'
            ]
        }
        return local_leagues.get(self.region, [])

    async def _fetch_live_markets_with_stream(self) -> List[MarketData]:
        """Fetch live markets with streaming information"""
        try:
            params = {
                'region': self.region,
                'streaming': True,
                'liveOnly': True
            }
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/live-stream',
                params=params
            )
            
            markets = []
            for market_data in response.get('markets', []):
                aver_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['eventId'],
                    event_name=market_data['eventName'],
                    market_type=market_data.get('type', 'match_odds'),
                    selections=market_data.get('selections', []),
                    metadata={
                        'aver': {
                            'streaming_url': market_data.get('streamUrl'),
                            'stream_quality': market_data.get('streamQuality'),
                            'stream_available': True,
                            'live_odds_updates': market_data.get('liveOddsUpdates', True)
                        }
                    }
                )
                markets.append(aver_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching live markets with stream: {e}")
            return []

    async def _fetch_odds(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific market"""
        try:
            params = {
                'region': self.region,
                'currency': self.default_currency
            }
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/{market_id}/odds',
                params=params
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching odds for market {market_id}: {e}")
            return None

    async def _execute_cancel(self, bet_id: str) -> bool:
        """Cancel bet on Aver"""
        try:
            response = await self._make_request(
                'DELETE',
                f'{self.api_base_url}/v1/bets/{bet_id}'
            )
            
            return response.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Error cancelling bet {bet_id}: {e}")
            return False

    async def _finalize_initialization(self) -> bool:
        """Finalize Aver-specific initialization"""
        # Get account info with regional settings
        account_info = await self.get_account_info()
        if account_info:
            self.session_info.balance = account_info.get('balance', 0)
            self.session_info.currency = account_info.get('currency', self.default_currency)
            return True
        return False

    def get_supported_markets(self) -> List[str]:
        """Get Aver-supported market types"""
        regional_markets = {
            'africa': [
                'match_odds', 'asian_handicap', 'over_under',
                'correct_score', 'first_goal_scorer', 'half_time_result',
                'premier_league_specials', 'caf_specials'
            ],
            'asia': [
                'match_odds', 'asian_handicap', 'over_under',
                'correct_score', 'j_league_specials', 'k_league_specials',
                'esports_markets', 'table_tennis'
            ],
            'latam': [
                'match_odds', 'asian_handicap', 'over_under',
                'correct_score', 'copa_libertadores_specials', 'liga_mx_specials',
                'basketball', 'volleyball'
            ]
        }
        return regional_markets.get(self.region, ['match_odds'])

    async def get_balance(self) -> Optional[float]:
        """Get Aver account balance"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/account/balance?currency={self.default_currency}&region={self.region}'
            )
            
            return response.get('balance', 0)
            
        except Exception as e:
            self.logger.error(f"Error getting Aver balance: {e}")
            return None

    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed Aver account information"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/account/info?region={self.region}'
            )
            
            return {
                'currency': response.get('currency', self.default_currency),
                'balance': response.get('balance', 0),
                'region': self.region,
                'language': self.language,
                'payment_methods': response.get('paymentMethods', []),
                'verification_level': response.get('verificationLevel'),
                'mobile_betting_enabled': response.get('mobileBettingEnabled', True),
                'last_update': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Aver account info: {e}")
            return {}

    async def get_bet_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get Aver betting history"""
        try:
            params = {
                'region': self.region,
                'limit': limit,
                'currency': self.default_currency
            }
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/account/bets/history',
                params=params
            )
            
            return response.get('bets', [])
            
        except Exception as e:
            self.logger.error(f"Error getting Aver bet history: {e}")
            return []

    async def update_market_data(self, market_id: str) -> Optional[MarketData]:
        """Update market data for a specific market"""
        try:
            odds_data = await self._fetch_odds(market_id)
            if not odds_data:
                return None
            
            # Convert to standard format
            aver_market = MarketData(
                market_id=market_id,
                event_id=odds_data.get('eventId', ''),
                event_name=odds_data.get('eventName', ''),
                market_type=odds_data.get('type', 'match_odds'),
                selections=odds_data.get('selections', []),
                metadata={
                    'aver': {
                        'region': self.region,
                        'streaming_available': odds_data.get('streamingAvailable', False),
                        'local_start_time': odds_data.get('localStartTime'),
                        'mobile_optimized': odds_data.get('mobileOptimized', False)
                    }
                }
            )
            
            return aver_market
            
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
            return None

    # Aver-specific methods
    async def get_local_payment_methods(self) -> List[Dict[str, Any]]:
        """Get local payment methods for the region"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/account/payment-methods?region={self.region}'
            )
            
            return response.get('paymentMethods', [])
            
        except Exception as e:
            self.logger.error(f"Error getting local payment methods: {e}")
            return []

    async def initiate_mobile_money_payment(
        self,
        amount: float,
        provider: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """Initiate mobile money payment"""
        try:
            payment_data = {
                'amount': amount,
                'currency': self.default_currency,
                'provider': provider,
                'phoneNumber': phone_number,
                'region': self.region
            }
            
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/v1/payments/mobile-money',
                data=payment_data
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error initiating mobile money payment: {e}")
            return {}

    async def get_regional_sports_schedule(self, sport: str) -> List[Dict[str, Any]]:
        """Get regional sports schedule"""
        try:
            params = {
                'region': self.region,
                'sport': sport,
                'language': self.language
            }
            
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/sports/schedule',
                params=params
            )
            
            return response.get('events', [])
            
        except Exception as e:
            self.logger.error(f"Error getting regional sports schedule: {e}")
            return []

    async def get_live_stream_url(self, event_id: str) -> Optional[str]:
        """Get live stream URL for an event"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/streaming/event/{event_id}?region={self.region}'
            )
            
            return response.get('streamUrl')
            
        except Exception as e:
            self.logger.error(f"Error getting live stream URL: {e}")
            return None

    def calculate_regional_betting_limits(self, market_type: str, event_importance: int) -> Dict[str, float]:
        """Calculate betting limits based on region and market type"""
        base_limits = {
            'africa': {'min': 1.0, 'max': 500.0},
            'asia': {'min': 0.5, 'max': 1000.0},
            'latam': {'min': 1.0, 'max': 750.0}
        }
        
        region_limit = base_limits.get(self.region, base_limits['africa'])
        
        # Adjust based on market importance
        if event_importance > 7:  # High importance events
            region_limit['max'] *= 2
        elif event_importance < 3:  # Low importance events
            region_limit['max'] *= 0.5
        
        return region_limit

    def get_cultural_betting_preferences(self) -> Dict[str, Any]:
        """Get cultural betting preferences for the region"""
        preferences = {
            'africa': {
                'popular_markets': ['match_odds', 'asian_handicap', 'correct_score'],
                'preferred_bet_sizes': 'small_to_medium',
                'mobile_usage': 'high',
                'local_time_importance': 'high'
            },
            'asia': {
                'popular_markets': ['asian_handicap', 'over_under', 'esports'],
                'preferred_bet_sizes': 'medium',
                'mobile_usage': 'very_high',
                'cash_out_importance': 'high'
            },
            'latam': {
                'popular_markets': ['match_odds', 'both_teams_score', 'first_goal'],
                'preferred_bet_sizes': 'medium_to_large',
                'mobile_usage': 'high',
                'live_betting_importance': 'high'
            }
        }
        
        return preferences.get(self.region, preferences['africa'])

    async def _perform_health_check(self) -> bool:
        """Perform Aver-specific health check"""
        try:
            # Check regional API
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/health?region={self.region}'
            )
            
            return response.get('status') == 'ok'
            
        except:
            return False