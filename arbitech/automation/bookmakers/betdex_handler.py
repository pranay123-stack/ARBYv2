"""
BetDex Handler

Specialized handler for BetDex with cryptocurrency integration and unique interface handling.

BetDex-specific features:
- Cryptocurrency payments and settlements
- DeFi betting mechanisms
- Smart contract interactions
- Cross-chain compatibility
- DAO governance
- NFT betting markets
"""

import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
from web3 import Web3

from .handler_base import (
    BaseBookmakerHandler,
    BetRequest,
    BetResponse,
    MarketData,
    SessionInfo,
    OrderStatus,
    HandlerStatus
)


class BetDexHandler(BaseBookmakerHandler):
    """
    BetDex Cryptocurrency Betting Handler
    
    Handles BetDex-specific functionality including:
    - Cryptocurrency betting markets
    - Smart contract interactions
    - DeFi protocol integration
    - Cross-chain operations
    - NFT and metaverse betting
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize BetDex handler"""
        super().__init__(config)
        
        # BetDex-specific configuration
        self.api_base_url = config.get('api_base_url', 'https://api.betdex.com')
        self.web3_rpc_url = config.get('web3_rpc_url', 'https://mainnet.infura.io/v3/YOUR_KEY')
        self.private_key = config.get('private_key', '')
        self.wallet_address = config.get('wallet_address', '')
        self.chain_id = config.get('chain_id', 1)  # Ethereum mainnet by default
        
        # Supported cryptocurrencies
        self.supported_currencies = config.get('supported_currencies', [
            'ETH', 'USDC', 'USDT', 'BTC', 'DAI', 'WBTC', 'UNI'
        ])
        self.default_currency = config.get('default_currency', 'USDC')
        
        # Smart contract addresses
        self.betting_contract_address = config.get('betting_contract_address', '')
        self.token_contract_addresses = config.get('token_contract_addresses', {})
        
        # Web3 instance
        self.web3: Optional[Web3] = None
        
        # DeFi integration
        self.dex_router_address = config.get('dex_router_address', '')
        self.dex_factory_address = config.get('dex_factory_address', '')
        
        # Rate limiting for BetDex API
        self.rate_limiter.update({
            'requests_per_minute': 100,
            'requests_per_hour': 2000
        })

    def _get_bookmaker_name(self) -> str:
        """Get bookmaker name"""
        return "betdex"

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get BetDex-specific authentication headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add wallet signature if available
        if self.wallet_address:
            headers['X-Wallet-Address'] = self.wallet_address
        
        # Add API key if available
        if hasattr(self, 'api_key') and self.api_key:
            headers['X-API-Key'] = self.api_key
        
        return headers

    async def authenticate(self) -> bool:
        """Authenticate with BetDex"""
        try:
            self.logger.info("Authenticating with BetDex")
            
            # Initialize Web3 connection
            if not await self._initialize_web3():
                return False
            
            # Verify wallet ownership
            if not await self._verify_wallet_ownership():
                return False
            
            # Get session token
            session_token = await self._get_session_token()
            if session_token:
                self.session_info.session_token = session_token
                self.session_info.authenticated = True
                self.session_info.username = self.wallet_address
                self.session_info.user_id = self.wallet_address
                
                self.logger.info(f"Successfully authenticated with BetDex wallet: {self.wallet_address}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error authenticating with BetDex: {e}")
            return False

    async def _initialize_web3(self) -> bool:
        """Initialize Web3 connection"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.web3_rpc_url))
            
            if not self.web3.is_connected():
                self.logger.error("Failed to connect to blockchain network")
                return False
            
            # Check if account is available
            if self.private_key and not self.web3.eth.account.from_key(self.private_key):
                self.logger.error("Invalid private key")
                return False
            
            self.logger.info("Web3 connection initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing Web3: {e}")
            return False

    async def _verify_wallet_ownership(self) -> bool:
        """Verify wallet ownership by signing a message"""
        try:
            if not self.web3 or not self.private_key:
                return False
            
            # Generate random message
            message = f"BetDex authentication: {int(time.time())}"
            message_hash = self.web3.eth.account.hash_message(message)
            
            # Sign message
            account = self.web3.eth.account.from_key(self.private_key)
            signature = account.signHash(message_hash)
            
            # Verify signature
            recovered_address = self.web3.eth.account.recoverHash(message_hash, signature=signature.signature)
            
            if recovered_address.lower() == self.wallet_address.lower():
                self.logger.info("Wallet ownership verified")
                return True
            else:
                self.logger.error("Wallet ownership verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying wallet ownership: {e}")
            return False

    async def _get_session_token(self) -> Optional[str]:
        """Get session token from BetDex"""
        try:
            # This would typically involve signing a transaction or message
            # For now, return a mock token
            return f"betdex_session_{self.wallet_address}_{int(time.time())}"
            
        except Exception as e:
            self.logger.error(f"Error getting session token: {e}")
            return None

    async def _execute_bet(self, bet_request: BetRequest) -> BetResponse:
        """Execute bet placement on BetDex"""
        try:
            # Convert to BetDex format
            betdex_request = self._convert_to_betdex_format(bet_request)
            
            # Execute blockchain transaction if required
            if betdex_request.get('requires_blockchain_transaction', False):
                tx_hash = await self._execute_blockchain_transaction(betdex_request)
                if tx_hash:
                    return BetResponse(
                        success=True,
                        bet_id=tx_hash,
                        status=OrderStatus.SUBMITTED,
                        odds=bet_request.odds,
                        stake=bet_request.stake,
                        metadata={'blockchain_tx': tx_hash, 'betdex': betdex_request}
                    )
                else:
                    return BetResponse(
                        success=False,
                        error_message="Blockchain transaction failed"
                    )
            
            # Use API placement
            response = await self._make_request(
                'POST',
                f'{self.api_base_url}/v1/bets',
                data=betdex_request
            )
            
            if response.get('success', False):
                return BetResponse(
                    success=True,
                    bet_id=response.get('betId'),
                    status=OrderStatus.SUBMITTED,
                    odds=bet_request.odds,
                    stake=bet_request.stake,
                    metadata={'betdex': response}
                )
            
            return BetResponse(
                success=False,
                error_message=response.get('error', 'Unknown error')
            )
            
        except Exception as e:
            self.logger.error(f"Error executing bet on BetDex: {e}")
            return BetResponse(
                success=False,
                error_message=str(e)
            )

    def _convert_to_betdex_format(self, bet_request: BetRequest) -> Dict[str, Any]:
        """Convert standard bet request to BetDex format"""
        betdex_request = {
            'marketId': bet_request.market_id,
            'selectionId': bet_request.selection_id,
            'odds': str(bet_request.odds),
            'stake': str(bet_request.stake),
            'currency': self.default_currency,
            'walletAddress': self.wallet_address,
            'timestamp': int(time.time()),
            'betType': bet_request.bet_type.upper(),
            'metadata': {
                'eventId': bet_request.event_id,
                'eventName': bet_request.event_name,
                'marketType': bet_request.market_type,
                'original_metadata': bet_request.metadata
            }
        }
        
        # Add DeFi-specific parameters
        if bet_request.market_type in ['defi_yield', 'liquidity_mining']:
            betdex_request['defiProtocol'] = bet_request.metadata.get('protocol')
            betdex_request['yieldApy'] = bet_request.metadata.get('apy')
        
        # Add NFT betting parameters
        if bet_request.market_type in ['nft_floor_price', 'nft_volume']:
            betdex_request['nftCollection'] = bet_request.metadata.get('collection_address')
            betdex_request['nftMetadata'] = bet_request.metadata.get('metadata')
        
        # Check if blockchain transaction is required
        betdex_request['requires_blockchain_transaction'] = (
            bet_request.stake > 100 or  # High stake transactions
            bet_request.market_type.startswith('defi_') or
            bet_request.market_type.startswith('nft_')
        )
        
        return betdex_request

    async def _execute_blockchain_transaction(self, betdex_request: Dict[str, Any]) -> Optional[str]:
        """Execute blockchain transaction for betting"""
        try:
            if not self.web3 or not self.private_key:
                return None
            
            # Get gas price and estimate gas
            gas_price = self.web3.eth.gas_price
            gas_estimate = 150000  # Estimated gas for betting contract
            
            # Build transaction (this would depend on actual contract ABI)
            transaction = {
                'to': self.betting_contract_address,
                'value': self.web3.to_wei(betdex_request['stake'], 'ether'),
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.wallet_address),
                'chainId': self.chain_id
            }
            
            # Sign transaction
            account = self.web3.eth.account.from_key(self.private_key)
            signed_txn = account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash.hex())
            
            if receipt.status == 1:  # Success
                self.logger.info(f"Blockchain transaction successful: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                self.logger.error(f"Blockchain transaction failed: {receipt.transactionHash.hex()}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing blockchain transaction: {e}")
            return None

    async def _fetch_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch available markets from BetDex"""
        try:
            markets = []
            
            # Fetch traditional sports markets
            sports_markets = await self._fetch_sports_markets(filters)
            markets.extend(sports_markets)
            
            # Fetch DeFi betting markets
            if filters.get('include_defi', True):
                defi_markets = await self._fetch_defi_markets()
                markets.extend(defi_markets)
            
            # Fetch NFT betting markets
            if filters.get('include_nft', True):
                nft_markets = await self._fetch_nft_markets()
                markets.extend(nft_markets)
            
            # Fetch esports markets
            esports_markets = await self._fetch_esports_markets()
            markets.extend(esports_markets)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching BetDex markets: {e}")
            return []

    async def _fetch_sports_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch sports betting markets"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/sports?sportId=football&currency={self.default_currency}'
            )
            
            markets = []
            for market_data in response.get('markets', []):
                betdex_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['eventId'],
                    event_name=market_data['eventName'],
                    market_type='match_odds',
                    selections=market_data.get('selections', []),
                    metadata={
                        'betdex': {
                            'currency': market_data.get('currency'),
                            'pool_size': market_data.get('poolSize'),
                            'protocol_type': 'traditional'
                        }
                    }
                )
                markets.append(betdex_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching sports markets: {e}")
            return []

    async def _fetch_defi_markets(self) -> List[MarketData]:
        """Fetch DeFi betting markets"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/defi?currency={self.default_currency}'
            )
            
            markets = []
            for market_data in response.get('markets', []):
                betdex_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['protocolId'],
                    event_name=market_data['protocolName'],
                    market_type=f"defi_{market_data.get('marketType', 'yield')}",
                    selections=market_data.get('selections', []),
                    metadata={
                        'betdex': {
                            'protocol': market_data.get('protocol'),
                            'apy': market_data.get('apy'),
                            'tvl': market_data.get('tvl'),
                            'currency': market_data.get('currency'),
                            'protocol_type': 'defi'
                        }
                    }
                )
                markets.append(betdex_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching DeFi markets: {e}")
            return []

    async def _fetch_nft_markets(self) -> List[MarketData]:
        """Fetch NFT betting markets"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/nft?currency={self.default_currency}'
            )
            
            markets = []
            for market_data in response.get('markets', []):
                betdex_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['collectionAddress'],
                    event_name=market_data['collectionName'],
                    market_type=f"nft_{market_data.get('marketType', 'floor_price')}",
                    selections=market_data.get('selections', []),
                    metadata={
                        'betdex': {
                            'collection_address': market_data.get('collectionAddress'),
                            'total_supply': market_data.get('totalSupply'),
                            'floor_price': market_data.get('floorPrice'),
                            'volume_24h': market_data.get('volume24h'),
                            'protocol_type': 'nft'
                        }
                    }
                )
                markets.append(betdex_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching NFT markets: {e}")
            return []

    async def _fetch_esports_markets(self) -> List[MarketData]:
        """Fetch esports betting markets"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/esports?currency={self.default_currency}'
            )
            
            markets = []
            for market_data in response.get('markets', []):
                betdex_market = MarketData(
                    market_id=market_data['id'],
                    event_id=market_data['eventId'],
                    event_name=market_data['eventName'],
                    market_type='esports_match_odds',
                    selections=market_data.get('selections', []),
                    metadata={
                        'betdex': {
                            'game': market_data.get('game'),
                            'tournament': market_data.get('tournament'),
                            'currency': market_data.get('currency'),
                            'protocol_type': 'esports'
                        }
                    }
                )
                markets.append(betdex_market)
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching esports markets: {e}")
            return []

    async def _fetch_odds(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific market"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/markets/{market_id}/odds'
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching odds for market {market_id}: {e}")
            return None

    async def _execute_cancel(self, bet_id: str) -> bool:
        """Cancel bet on BetDex"""
        try:
            # Check if it's a blockchain transaction
            if len(bet_id) == 66 and bet_id.startswith('0x'):  # Transaction hash format
                # Cancel blockchain transaction (complex implementation)
                return await self._cancel_blockchain_bet(bet_id)
            else:
                # Cancel via API
                response = await self._make_request(
                    'DELETE',
                    f'{self.api_base_url}/v1/bets/{bet_id}'
                )
                return response.get('success', False)
                
        except Exception as e:
            self.logger.error(f"Error cancelling bet {bet_id}: {e}")
            return False

    async def _cancel_blockchain_bet(self, tx_hash: str) -> bool:
        """Cancel blockchain bet (complex implementation)"""
        try:
            # This would involve calling a smart contract function
            # Placeholder implementation
            self.logger.warning("Blockchain bet cancellation not fully implemented")
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling blockchain bet: {e}")
            return False

    async def _finalize_initialization(self) -> bool:
        """Finalize BetDex-specific initialization"""
        # Get account balance
        balance = await self.get_balance()
        if balance is not None:
            self.session_info.balance = balance
            self.session_info.currency = self.default_currency
            return True
        return False

    def get_supported_markets(self) -> List[str]:
        """Get BetDex-supported market types"""
        return [
            'match_odds',
            'asian_handicap',
            'over_under',
            'correct_score',
            'defi_yield',
            'defi_liquidity',
            'nft_floor_price',
            'nft_volume',
            'metaverse_land',
            'esports_match_odds',
            'crypto_prediction',
            'dao_governance'
        ]

    async def get_balance(self) -> Optional[float]:
        """Get BetDex account balance"""
        try:
            if self.default_currency == 'ETH':
                # Get ETH balance
                balance_wei = self.web3.eth.get_balance(self.wallet_address)
                balance_eth = self.web3.from_wei(balance_wei, 'ether')
                return float(balance_eth)
            else:
                # Get ERC20 token balance
                response = await self._make_request(
                    'GET',
                    f'{self.api_base_url}/v1/wallet/balance/{self.wallet_address}?currency={self.default_currency}'
                )
                return response.get('balance', 0)
            
        except Exception as e:
            self.logger.error(f"Error getting BetDex balance: {e}")
            return None

    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed BetDex account information"""
        try:
            balances = {}
            
            # Get ETH balance
            if self.web3:
                try:
                    eth_balance_wei = self.web3.eth.get_balance(self.wallet_address)
                    balances['ETH'] = float(self.web3.from_wei(eth_balance_wei, 'ether'))
                except:
                    balances['ETH'] = 0
            
            # Get other token balances
            for currency in self.supported_currencies:
                if currency != 'ETH':
                    try:
                        response = await self._make_request(
                            'GET',
                            f'{self.api_base_url}/v1/wallet/balance/{self.wallet_address}?currency={currency}'
                        )
                        balances[currency] = response.get('balance', 0)
                    except:
                        balances[currency] = 0
            
            return {
                'wallet_address': self.wallet_address,
                'balances': balances,
                'default_currency': self.default_currency,
                'chain_id': self.chain_id,
                'last_update': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting BetDex account info: {e}")
            return {}

    async def get_bet_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get BetDex betting history"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/bets/history?wallet={self.wallet_address}&limit={limit}'
            )
            
            return response.get('bets', [])
            
        except Exception as e:
            self.logger.error(f"Error getting BetDex bet history: {e}")
            return []

    async def update_market_data(self, market_id: str) -> Optional[MarketData]:
        """Update market data for a specific market"""
        try:
            odds_data = await self._fetch_odds(market_id)
            if not odds_data:
                return None
            
            # Convert to standard format
            betdex_market = MarketData(
                market_id=market_id,
                event_id=odds_data.get('eventId', ''),
                event_name=odds_data.get('eventName', ''),
                market_type=odds_data.get('marketType', 'match_odds'),
                selections=odds_data.get('selections', []),
                metadata={
                    'betdex': odds_data.get('metadata', {})
                }
            )
            
            return betdex_market
            
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
            return None

    # BetDex-specific methods
    async def swap_tokens(self, from_token: str, to_token: str, amount: float) -> Optional[str]:
        """Swap tokens using integrated DEX"""
        try:
            # This would integrate with Uniswap, SushiSwap, etc.
            # Placeholder implementation
            return f"swap_{int(time.time())}"
            
        except Exception as e:
            self.logger.error(f"Error swapping tokens: {e}")
            return None

    async def stake_tokens(self, token: str, amount: float) -> Optional[str]:
        """Stake tokens for yield farming"""
        try:
            # This would involve calling staking contracts
            # Placeholder implementation
            return f"stake_{int(time.time())}"
            
        except Exception as e:
            self.logger.error(f"Error staking tokens: {e}")
            return None

    async def get_defi_protocol_stats(self, protocol: str) -> Dict[str, Any]:
        """Get DeFi protocol statistics"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/protocols/{protocol}/stats'
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting DeFi protocol stats: {e}")
            return {}

    async def get_nft_collection_stats(self, collection_address: str) -> Dict[str, Any]:
        """Get NFT collection statistics"""
        try:
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/nft/collection/{collection_address}/stats'
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting NFT collection stats: {e}")
            return {}

    def calculate_crypto_volatility_adjusted_odds(self, base_odds: float, volatility: float) -> float:
        """Calculate odds adjusted for crypto market volatility"""
        volatility_adjustment = 1 + (volatility * 0.1)  # 10% volatility impact
        return base_odds * volatility_adjustment

    def get_max_crypto_stake(self, currency: str, odds: float) -> float:
        """Get maximum stake based on currency and odds"""
        currency_limits = {
            'ETH': 100.0,
            'USDC': 50000.0,
            'USDT': 50000.0,
            'BTC': 10.0,
            'DAI': 50000.0
        }
        
        base_limit = currency_limits.get(currency, 1000.0)
        
        # Adjust limit based on odds
        if odds > 10:
            return base_limit * 0.5
        elif odds > 5:
            return base_limit * 0.75
        else:
            return base_limit

    async def _perform_health_check(self) -> bool:
        """Perform BetDex-specific health check"""
        try:
            # Check Web3 connection
            if not self.web3 or not self.web3.is_connected():
                return False
            
            # Check API connectivity
            response = await self._make_request(
                'GET',
                f'{self.api_base_url}/v1/health'
            )
            
            return response.get('status') == 'ok'
            
        except:
            return False