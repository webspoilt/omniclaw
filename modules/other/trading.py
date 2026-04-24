#!/usr/bin/env python3
"""
OmniClaw Trading Interface
Connects to trading platforms for automated trading
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time
import json

logger = logging.getLogger("OmniClaw.Trading")


class TradingPlatform(Enum):
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    ALPACA = "alpaca"
    TRADING212 = "trading212"
    CUSTOM = "custom"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Represents a trading order"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    status: str = "pending"
    created_at: float = 0
    filled_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    opened_at: float


@dataclass
class MarketData:
    """Represents market data"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: float


class TradingInterface:
    """
    Unified trading interface for multiple platforms
    Supports crypto and stock trading
    """
    
    def __init__(self, platform: TradingPlatform, config: Dict[str, Any]):
        self.platform = platform
        self.config = config
        self.client = None
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.market_data: Dict[str, MarketData] = {}
        self.price_callbacks: List[Callable[[str, float], None]] = []
        self.running = False
        self.price_stream_task = None
        
        # Initialize client
        self._initialize_client()
        
        logger.info(f"Trading interface initialized for {platform.value}")
    
    def _initialize_client(self):
        """Initialize the trading platform client"""
        if self.platform == TradingPlatform.BINANCE:
            try:
                import ccxt
                self.client = ccxt.binance({
                    'apiKey': self.config.get('api_key'),
                    'secret': self.config.get('api_secret'),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': self.config.get('market_type', 'spot'),
                    }
                })
            except ImportError:
                logger.error("ccxt not installed. Run: pip install ccxt")
                
        elif self.platform == TradingPlatform.COINBASE:
            try:
                import ccxt
                self.client = ccxt.coinbase({
                    'apiKey': self.config.get('api_key'),
                    'secret': self.config.get('api_secret'),
                    'password': self.config.get('passphrase'),
                })
            except ImportError:
                logger.error("ccxt not installed")
                
        elif self.platform == TradingPlatform.ALPACA:
            try:
                import alpaca_trade_api as tradeapi
                self.client = tradeapi.REST(
                    self.config.get('api_key'),
                    self.config.get('api_secret'),
                    base_url=self.config.get('base_url', 'https://paper-api.alpaca.markets')
                )
            except ImportError:
                logger.error("alpaca-trade-api not installed")
                
        elif self.platform == TradingPlatform.CUSTOM:
            # Custom API integration
            self.client = CustomTradingClient(self.config)
    
    async def start(self):
        """Start trading interface"""
        self.running = True
        
        # Start price stream
        self.price_stream_task = asyncio.create_task(self._price_stream_loop())
        
        logger.info("Trading interface started")
    
    async def stop(self):
        """Stop trading interface"""
        self.running = False
        
        if self.price_stream_task:
            self.price_stream_task.cancel()
        
        logger.info("Trading interface stopped")
    
    async def _price_stream_loop(self):
        """Background loop for price updates"""
        symbols = self.config.get('watch_symbols', ['BTC/USDT', 'ETH/USDT'])
        
        while self.running:
            try:
                for symbol in symbols:
                    data = await self.get_market_data(symbol)
                    if data:
                        self.market_data[symbol] = data
                        
                        # Notify callbacks
                        for callback in self.price_callbacks:
                            callback(symbol, data.price)
                
                await asyncio.sleep(self.config.get('update_interval', 5))
                
            except Exception as e:
                logger.error(f"Price stream error: {e}")
                await asyncio.sleep(10)
    
    def add_price_callback(self, callback: Callable[[str, float], None]):
        """Add price update callback"""
        self.price_callbacks.append(callback)
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if hasattr(self.client, 'fetch_balance'):
                balance = self.client.fetch_balance()
                return balance.get('total', {})
            elif hasattr(self.client, 'get_account'):
                account = self.client.get_account()
                return {
                    'cash': float(account.cash),
                    'portfolio_value': float(account.portfolio_value),
                }
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
    
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get market data for symbol"""
        try:
            if hasattr(self.client, 'fetch_ticker'):
                ticker = self.client.fetch_ticker(symbol)
                return MarketData(
                    symbol=symbol,
                    price=ticker['last'],
                    bid=ticker['bid'],
                    ask=ticker['ask'],
                    volume_24h=ticker.get('quoteVolume', 0),
                    change_24h=ticker.get('percentage', 0),
                    high_24h=ticker.get('high', 0),
                    low_24h=ticker.get('low', 0),
                    timestamp=ticker['timestamp'] / 1000
                )
            elif hasattr(self.client, 'get_latest_trade'):
                trade = self.client.get_latest_trade(symbol)
                return MarketData(
                    symbol=symbol,
                    price=float(trade.price),
                    bid=float(trade.price) * 0.999,
                    ask=float(trade.price) * 1.001,
                    volume_24h=0,
                    change_24h=0,
                    high_24h=0,
                    low_24h=0,
                    timestamp=time.time()
                )
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return None
    
    async def place_order(self, order: Order) -> Order:
        """Place a trading order"""
        try:
            if hasattr(self.client, 'create_order'):
                result = self.client.create_order(
                    symbol=order.symbol,
                    type=order.order_type.value,
                    side=order.side.value,
                    amount=order.quantity,
                    price=order.price
                )
                
                order.order_id = result.get('id')
                order.status = result.get('status', 'open')
                
            elif hasattr(self.client, 'submit_order'):
                result = self.client.submit_order(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=order.side.value,
                    type=order.order_type.value,
                    limit_price=order.price,
                    stop_price=order.stop_price
                )
                
                order.order_id = result.id
                order.status = result.status
            
            self.orders[order.order_id] = order
            logger.info(f"Order placed: {order.order_id}")
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            order.status = "failed"
            return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            if hasattr(self.client, 'cancel_order'):
                self.client.cancel_order(order_id)
            elif hasattr(self.client, 'cancel_order'):
                self.client.cancel_order(order_id)
            
            if order_id in self.orders:
                self.orders[order_id].status = "canceled"
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            positions = []
            
            if hasattr(self.client, 'fetch_positions'):
                raw_positions = self.client.fetch_positions()
                for pos in raw_positions:
                    if pos.get('contracts', 0) != 0:
                        positions.append(Position(
                            symbol=pos['symbol'],
                            quantity=pos['contracts'],
                            avg_price=pos.get('entryPrice', 0),
                            current_price=pos.get('markPrice', 0),
                            unrealized_pnl=pos.get('unrealizedPnl', 0),
                            realized_pnl=pos.get('realizedPnl', 0),
                            opened_at=time.time()
                        ))
            
            elif hasattr(self.client, 'list_positions'):
                raw_positions = self.client.list_positions()
                for pos in raw_positions:
                    positions.append(Position(
                        symbol=pos.symbol,
                        quantity=float(pos.qty),
                        avg_price=float(pos.avg_entry_price),
                        current_price=float(pos.current_price),
                        unrealized_pnl=float(pos.unrealized_pl),
                        realized_pnl=float(pos.realized_pl),
                        opened_at=time.time()
                    ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_order_history(self, limit: int = 50) -> List[Order]:
        """Get order history"""
        try:
            if hasattr(self.client, 'fetch_orders'):
                orders = self.client.fetch_orders(limit=limit)
                return [
                    Order(
                        symbol=o['symbol'],
                        side=OrderSide(o['side']),
                        order_type=OrderType(o['type']),
                        quantity=o['amount'],
                        price=o.get('price'),
                        order_id=o['id'],
                        status=o['status']
                    )
                    for o in orders
                ]
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            return []
    
    async def execute_strategy(self, strategy: Dict[str, Any]):
        """Execute a trading strategy"""
        strategy_type = strategy.get('type', 'simple')
        
        if strategy_type == 'dca':
            await self._execute_dca_strategy(strategy)
        elif strategy_type == 'grid':
            await self._execute_grid_strategy(strategy)
        elif strategy_type == 'momentum':
            await self._execute_momentum_strategy(strategy)
        else:
            logger.warning(f"Unknown strategy type: {strategy_type}")
    
    async def _execute_dca_strategy(self, config: Dict[str, Any]):
        """Execute Dollar-Cost Averaging strategy"""
        symbol = config.get('symbol', 'BTC/USDT')
        amount = config.get('amount', 100)
        interval = config.get('interval', 86400)  # Daily
        
        logger.info(f"Starting DCA strategy for {symbol}")
        
        while self.running:
            try:
                # Place market buy order
                order = Order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=amount
                )
                
                await self.place_order(order)
                logger.info(f"DCA order placed: {amount} {symbol}")
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"DCA strategy error: {e}")
                await asyncio.sleep(60)
    
    async def _execute_grid_strategy(self, config: Dict[str, Any]):
        """Execute grid trading strategy"""
        # Placeholder for grid strategy
        pass
    
    async def _execute_momentum_strategy(self, config: Dict[str, Any]):
        """Execute momentum trading strategy"""
        # Placeholder for momentum strategy
        pass


class CustomTradingClient:
    """Custom trading API client"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
    
    async def request(self, method: str, endpoint: str, data: Dict = None):
        """Make API request"""
        import aiohttp
        
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=data
            ) as resp:
                return await resp.json()
